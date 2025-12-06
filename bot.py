import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_NAMESPACE_ID = os.environ["CF_NAMESPACE_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]
WORKER_BASE_URL = os.getenv("WORKER_BASE_URL", "https://example.workers.dev")

# user_id -> 临时图包数据
current_albums = {}
COUNTER_KEY = "__counter"


# ---------- Cloudflare KV ----------
def kv_headers():
    return {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "text/plain",
    }

def kv_base_url():
    return f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}"

def kv_get(key: str):
    url = f"{kv_base_url()}/values/{key}"
    resp = requests.get(url, headers=kv_headers())
    return resp.text if resp.status_code == 200 else None

def kv_put(key: str, value: str):
    url = f"{kv_base_url()}/values/{key}"
    resp = requests.put(url, headers=kv_headers(), data=value.encode("utf-8"))
    return resp.status_code == 200

def next_code() -> str:
    cur = kv_get(COUNTER_KEY)
    if cur is None:
        n = 1
    else:
        try:
            n = int(cur) + 1
        except ValueError:
            n = 1

    kv_put(COUNTER_KEY, str(n))

    if n < 10:
        return f"a0{n}"
    return f"a{n}"


# ---------- Bot 逻辑 ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 写真图包 Bot 已就绪\n\n"
        "/start_album  开始新图包\n"
        "#标题          第一条以 # 开头的消息作为标题\n"
        "发送图片       本套写真所有图片（可一次拖很多张）\n"
        "/set_pass 1234 可选：给当前图包设置访问密码\n"
        "发送文件       可选：zip/apk/txt等，会作为下载文件\n"
        "/end_album     结束本套图包，生成链接\n"
    )

async def start_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    current_albums[uid] = {
        "title": None,
        "files": [],          # photo file_id 列表
        "attachments": [],    # 其他文件列表 {file_id, file_name}
        "zip": None,          # {file_id, file_name}
        "password": None,
    }
    await update.message.reply_text(
        "🟦 已开始新的图包\n"
        "请先发送标题（以 # 开头），例如：\n"
        "#布丁大法 - 超甜舒芙蕾 [60P／276MB]\n"
        "然后发送所有图片，可以一次拖很多张。\n"
        "如需设置访问密码，可发送：/set_pass 1234\n"
        "如需添加压缩包/APK/txt 等文件，直接发送文件。\n"
        "最后用 /end_album 结束本套图包。"
    )

async def end_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        await update.message.reply_text("你还没有开始图包，请先发送 /start_album")
        return

    title = album["title"]
    files = album["files"]

    if not title:
        await update.message.reply_text("还没有标题（需要一条以 # 开头的消息）")
        return
    if not files:
        await update.message.reply_text("你还没有发送任何图片。")
        return

    try:
        code = next_code()
    except Exception as e:
        logger.exception("生成序列码失败")
        await update.message.reply_text("生成序列码失败，请稍后重试。")
        return

    data = {
        "title": title,
        "files": files,
        "attachments": album["attachments"],
        "zip": album["zip"],
        "password": album["password"],
    }

    ok = kv_put(code, json.dumps(data, ensure_ascii=False))
    if not ok:
        await update.message.reply_text("❌ 写入图包数据失败，请稍后再试。")
        return

    del current_albums[uid]

    link = f"{WORKER_BASE_URL}/{code}"
    await update.message.reply_text(
        f"🎉 图包已创建！\n"
        f"序列码：{code}\n"
        f"访问链接：{link}\n\n"
        f"你可以在网页打开，也可以访问 {WORKER_BASE_URL}/list 查看全部图包。"
    )

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        return

    text = (update.message.text or "").strip()
    if text.startswith("#") and album["title"] is None:
        album["title"] = text[1:].strip()
        await update.message.reply_text(
            f"✅ 标题已设置为：{album['title']}\n"
            f"现在请继续发送本套写真所有图片。"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        return
    photos = update.message.photo
    if not photos:
        return
    best = photos[-1]
    file_id = best.file_id
    album["files"].append(file_id)
    logger.info(f"Add photo {file_id}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        return

    doc = update.message.document
    if not doc:
        return

    file_id = doc.file_id
    file_name = doc.file_name or "file"
    mime_type = doc.mime_type or "application/octet-stream"

    # 记录到 attachments
    album["attachments"].append({
        "file_id": file_id,
        "file_name": file_name,
        "mime_type": mime_type,
    })
    logger.info(f"Add document {file_name} ({file_id})")

    # 如是 zip/7z/rar，则设为 zip（仅第一次）
    lname = file_name.lower()
    if album["zip"] is None and (lname.endswith(".zip") or lname.endswith(".7z") or lname.endswith(".rar")):
        album["zip"] = {
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
        }
        await update.message.reply_text(f"🎁 已设此文件为压缩包下载：{file_name}")

async def set_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        await update.message.reply_text("当前没有正在创建的图包，请先 /start_album。")
        return

    text = update.message.text or ""
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("用法：/set_pass 你的密码\n例如：/set_pass 1234")
        return

    password = parts[1].strip()
    album["password"] = password
    await update.message.reply_text(f"🔒 已为当前图包设置密码：{password}\n访问网页时需要输入该密码。")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start_album", start_album))
    app.add_handler(CommandHandler("end_album", end_album))
    app.add_handler(CommandHandler("set_pass", set_pass))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_title))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()


if __name__ == "__main__":
    main()
