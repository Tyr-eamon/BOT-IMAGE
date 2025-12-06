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
# user_id -> 待确认删除的图包代码
pending_deletes = {}
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

def kv_delete(key: str):
    url = f"{kv_base_url()}/values/{key}"
    resp = requests.delete(url, headers=kv_headers())
    return resp.status_code in (200, 204)

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
        "/delete a01    删除指定图包（yes/no 确认）\n"
    )

async def start_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    current_albums[uid] = {
        "title": None,
        "files": [],
        "attachments": [],
        "zip": None,
        "password": None,
    }
    await update.message.reply_text(
        "🟦 已开始新的图包\n"
        "请发送标题（以 # 开头），例如：\n"
        "#布丁大法 - 超甜舒芙蕾 [60P／276MB]\n"
        "然后发送所有图片，可以一次拖很多张。\n"
        "如需设置密码请发送：/set_pass 1234\n"
        "最后用 /end_album 结束本套图包。"
    )

async def end_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        await update.message.reply_text("请先发送 /start_album")
        return

    if not album["title"]:
        await update.message.reply_text("你还没有发送标题（需要以 # 开头）")
        return
    if not album["files"]:
        await update.message.reply_text("你还没有发送任何图片。")
        return

    try:
        code = next_code()
    except Exception:
        await update.message.reply_text("生成序列码失败，请稍后再试。")
        return

    data = json.dumps(album, ensure_ascii=False)
    ok = kv_put(code, data)
    if not ok:
        await update.message.reply_text("❌ 写入图包失败，请稍后再试。")
        return

    del current_albums[uid]

    await update.message.reply_text(
        f"🎉 图包已创建！\n"
        f"序列码：{code}\n"
        f"访问链接：{WORKER_BASE_URL}/{code}"
    )

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    text = (update.message.text or "").strip()

    if not album:
        if text.startswith("#"):
            await update.message.reply_text("请先发送 /start_album 开始新图包")
        return

    if not text.startswith("#"):
        return

    if album["title"] is not None:
        await update.message.reply_text(
            f"标题已设置为：{album['title']}"
        )
        return

    album["title"] = text[1:].strip()
    await update.message.reply_text(
        f"✅ 标题已设置为：{album['title']}\n请继续发送图片。"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        return
    best = update.message.photo[-1]
    album["files"].append(best.file_id)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        return

    doc = update.message.document
    file_id = doc.file_id
    fname = doc.file_name or "file"
    mime = doc.mime_type or "application/octet-stream"

    album["attachments"].append({
        "file_id": file_id,
        "file_name": fname,
        "mime_type": mime,
    })

    lname = fname.lower()
    if album["zip"] is None and (lname.endswith(".zip") or lname.endswith(".7z") or lname.endswith(".rar")):
        album["zip"] = {
            "file_id": file_id,
            "file_name": fname,
            "mime_type": mime,
        }
        await update.message.reply_text(f"🎁 已设 {fname} 为压缩包下载文件")

async def set_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        await update.message.reply_text("请先 /start_album 再设置密码。")
        return

    parts = update.message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("用法：/set_pass 密码")
        return

    album["password"] = parts[1]
    await update.message.reply_text(f"🔒 当前图包密码已设置为：{parts[1]}")

async def delete_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    parts = update.message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("用法：/delete a01")
        return

    code = parts[1].strip().lower()
    album_data = kv_get(code)
    if not album_data:
        await update.message.reply_text(f"❌ 图包不存在：{code}")
        return

    album = json.loads(album_data)
    title = album.get("title", "未知标题")
    count = len(album.get("files", []))

    pending_deletes[uid] = code

    await update.message.reply_text(
        f"📋 图包信息：\n"
        f"序列码：{code}\n"
        f"标题：{title}\n"
        f"图片数：{count}\n\n"
        f"确定删除吗？（yes/no）"
    )

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in pending_deletes:
        return

    text = (update.message.text or "").strip().lower()
    if text not in ("yes", "no"):
        await update.message.reply_text("请回复 yes 或 no")
        return

    code = pending_deletes[uid]

    if text == "no":
        del pending_deletes[uid]
        await update.message.reply_text("❌ 已取消删除。")
        return

    ok = kv_delete(code)
    del pending_deletes[uid]

    if ok:
        await update.message.reply_text(f"✅ 已成功删除图包：{code}")
    else:
        await update.message.reply_text("❌ 删除失败，请稍后再试。")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start_album", start_album))
    app.add_handler(CommandHandler("end_album", end_album))
    app.add_handler(CommandHandler("set_pass", set_pass))
    app.add_handler(CommandHandler("delete", delete_album))

    # 删除确认（优先处理）
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^(?i)(yes|no)$"),
            handle_confirmation
        )
    )

    # 标题（# 开头）
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^#"),
            handle_title
        )
    )

    # 图片
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # 文件
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
