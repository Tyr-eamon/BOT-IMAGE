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

# 你的 Telegram ID（超级管理员）
OWNER_ID = 8040798522  

# 白名单（允许使用 bot 的用户）
ALLOWED_USERS = set([OWNER_ID])

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


# ---------- 权限检查 ----------
def is_allowed(uid: int) -> bool:
    return uid == OWNER_ID or uid in ALLOWED_USERS

async def ensure_allowed(update: Update):
    uid = update.effective_user.id
    if not is_allowed(uid):
        await update.message.reply_text("❌ 你没有权限使用此 Bot。")
        return False
    return True


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
    if not await ensure_allowed(update): return
    await update.message.reply_text(
        "📸 写真图包 Bot 已就绪\n\n"
        "/start_album  开始新图包\n"
        "#标题          设置图包标题\n"
        "发送图片       可一次拖几十张\n"
        "/set_pass 1234 设置访问密码\n"
        "/end_album     结束并生成图包\n"
        "/delete a01    删除图包（yes/no 确认）\n"
        "\n管理员命令：\n"
        "/allow <id> 添加白名单\n"
        "/deny <id> 移除白名单\n"
        "/list_users 查看白名单\n"
    )

async def start_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

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
        "请发送标题（以 # 开头）\n"
        "然后发送所有图片（可一次拖很多张）\n"
        "如需设置密码：/set_pass 1234\n"
        "结束图包：/end_album"
    )

async def end_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        await update.message.reply_text("请先发送 /start_album")
        return

    if not album["title"]:
        await update.message.reply_text("你还没有设置标题（需 # 开头）")
        return
    if not album["files"]:
        await update.message.reply_text("你还没有发送任何图片。")
        return

    code = next_code()

    ok = kv_put(code, json.dumps(album, ensure_ascii=False))
    if not ok:
        await update.message.reply_text("❌ 写入图包失败。")
        return

    del current_albums[uid]

    await update.message.reply_text(
        f"🎉 图包已创建！\n"
        f"序列码：{code}\n"
        f"访问：{WORKER_BASE_URL}/{code}"
    )

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

    uid = update.effective_user.id
    album = current_albums.get(uid)
    text = update.message.text.strip()

    if not album:
        if text.startswith("#"):
            await update.message.reply_text("请先 /start_album")
        return

    if not text.startswith("#"):
        return

    if album["title"] is not None:
        await update.message.reply_text(f"标题已设置为：{album['title']}")
        return

    album["title"] = text[1:].strip()
    await update.message.reply_text(f"标题已设置为：{album['title']}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album: return

    best = update.message.photo[-1]
    album["files"].append(best.file_id)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album: return

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
    if album["zip"] is None and (lname.endswith(".zip") or lname.endswith(".rar") or lname.endswith(".7z")):
        album["zip"] = {
            "file_id": file_id,
            "file_name": fname,
            "mime_type": mime,
        }
        await update.message.reply_text(f"🎁 已设 {fname} 为压缩包文件")

async def set_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album:
        await update.message.reply_text("请先 /start_album")
        return

    parts = update.message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("用法：/set_pass 密码")
        return

    album["password"] = parts[1]
    await update.message.reply_text(f"密码已设置为：{parts[1]}")

async def delete_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return

    uid = update.effective_user.id
    parts = update.message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("用法：/delete a01")
        return

    code = parts[1].lower()
    album_data = kv_get(code)
    if not album_data:
        await update.message.reply_text(f"图包不存在：{code}")
        return

    album = json.loads(album_data)
    title = album.get("title", "未知标题")
    count = len(album.get("files", []))

    pending_deletes[uid] = code

    await update.message.reply_text(
        f"📋 图包信息：\n序列码：{code}\n标题：{title}\n图片数：{count}\n\n"
        f"确定删除吗？（yes/no）"
    )

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in pending_deletes:
        return

    text = update.message.text.strip().lower()

    if text not in ("yes", "no"):
        await update.message.reply_text("请回复 yes 或 no")
        return

    code = pending_deletes[uid]

    if text == "no":
        del pending_deletes[uid]
        await update.message.reply_text("已取消删除。")
        return

    ok = kv_delete(code)
    del pending_deletes[uid]

    if ok:
        await update.message.reply_text(f"已删除图包：{code}")
    else:
        await update.message.reply_text("删除失败，请稍后再试。")


# ---------- 管理员命令（白名单） ----------

async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("❌ 只有管理员能管理用户。")
        return

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text("用法：/allow 用户ID")
        return

    try:
        target = int(parts[1])
    except:
        await update.message.reply_text("用户 ID 必须是数字。")
        return

    ALLOWED_USERS.add(target)
    await update.message.reply_text(f"✅ 已加入白名单：{target}")

async def deny_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("❌ 只有管理员能管理用户。")
        return

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text("用法：/deny 用户ID")
        return

    try:
        target = int(parts[1])
    except:
        await update.message.reply_text("用户 ID 必须是数字。")
        return

    if target in ALLOWED_USERS:
        ALLOWED_USERS.remove(target)

    await update.message.reply_text(f"⛔ 已移出白名单：{target}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("❌ 你没有权限查看用户列表。")
        return

    text = "\n".join(str(u) for u in ALLOWED_USERS)
    await update.message.reply_text(f"📋 白名单用户：\n{text}")


# ---------- 注册 ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 用户命令
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start_album", start_album))
    app.add_handler(CommandHandler("end_album", end_album))
    app.add_handler(CommandHandler("set_pass", set_pass))
    app.add_handler(CommandHandler("delete", delete_album))

    # 管理命令
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("deny", deny_user))
    app.add_handler(CommandHandler("list_users", list_users))

    # 删除确认（yes/no）必须最优先匹配
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^(?i)(yes|no)$"),
            handle_confirmation
        )
    )

    # 标题处理
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^#"),
            handle_title
        )
    )

    # 图片
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # 文件（zip、apk、txt 等）
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
