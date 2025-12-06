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
    return resp.status_code == 204

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
    logger.info(f"[start_album] User {uid} started a new album")
    current_albums[uid] = {
        "title": None,
        "files": [],          # photo file_id 列表
        "attachments": [],    # 其他文件列表 {file_id, file_name}
        "zip": None,          # {file_id, file_name}
        "password": None,
    }
    logger.info(f"[start_album] Album created for user {uid}: {current_albums[uid]}")
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
    text = (update.message.text or "").strip()
    
    logger.info(f"[handle_title] User {uid} sent: '{text}', album exists: {album is not None}")
    
    if not album:
        logger.info(f"[handle_title] No album for user {uid}, ignoring message")
        if text.startswith("#"):
            logger.info(f"[handle_title] User {uid} tried to set title without /start_album")
            await update.message.reply_text("请先发送 /start_album 开始新的图包")
        return

    if not text.startswith("#"):
        logger.info(f"[handle_title] Message does not start with #, ignoring")
        return
    
    if album["title"] is not None:
        logger.info(f"[handle_title] Title already set for user {uid}: '{album['title']}'")
        await update.message.reply_text(f"✅ 标题已设置为：{album['title']}\n(如需修改，请重新发送 /start_album)")
        return
    
    album["title"] = text[1:].strip()
    logger.info(f"[handle_title] Title set for user {uid}: '{album['title']}'")
    await update.message.reply_text(
        f"✅ 标题已设置为：{album['title']}\n"
        f"现在请继续发送本套写真所有图片。"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    logger.info(f"[handle_photo] User {uid} sent photo, album exists: {album is not None}")
    if not album:
        logger.info(f"[handle_photo] No album for user {uid}, ignoring photo")
        return
    photos = update.message.photo
    if not photos:
        logger.info(f"[handle_photo] No photos in message for user {uid}")
        return
    best = photos[-1]
    file_id = best.file_id
    album["files"].append(file_id)
    logger.info(f"[handle_photo] Added photo {file_id} for user {uid}, total photos: {len(album['files'])}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    logger.info(f"[handle_document] User {uid} sent document, album exists: {album is not None}")
    if not album:
        logger.info(f"[handle_document] No album for user {uid}, ignoring document")
        return

    doc = update.message.document
    if not doc:
        logger.info(f"[handle_document] No document in message for user {uid}")
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
    logger.info(f"[handle_document] Added document {file_name} ({file_id}) for user {uid}, total attachments: {len(album['attachments'])}")

    # 如是 zip/7z/rar，则设为 zip（仅第一次）
    lname = file_name.lower()
    if album["zip"] is None and (lname.endswith(".zip") or lname.endswith(".7z") or lname.endswith(".rar")):
        album["zip"] = {
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
        }
        logger.info(f"[handle_document] Set zip file for user {uid}: {file_name}")
        await update.message.reply_text(f"🎁 已设此文件为压缩包下载：{file_name}")

async def set_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    album = current_albums.get(uid)
    logger.info(f"[set_pass] User {uid} set password, album exists: {album is not None}")
    if not album:
        logger.info(f"[set_pass] No album for user {uid}")
        await update.message.reply_text("当前没有正在创建的图包，请先 /start_album。")
        return

    text = update.message.text or ""
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("用法：/set_pass 你的密码\n例如：/set_pass 1234")
        return

    password = parts[1].strip()
    album["password"] = password
    logger.info(f"[set_pass] Password set for user {uid}: {password}")
    await update.message.reply_text(f"🔒 已为当前图包设置密码：{password}\n访问网页时需要输入该密码。")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def delete_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text or ""
    parts = text.strip().split(maxsplit=1)
    
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ 请输入正确的序列码，例如：/delete a01"
        )
        return
    
    code = parts[1].strip().lower()
    
    if not code:
        await update.message.reply_text(
            "❌ 请输入正确的序列码，例如：/delete a01"
        )
        return
    
    album_data = kv_get(code)
    if album_data is None:
        await update.message.reply_text(f"❌ 图包不存在：{code}")
        return
    
    try:
        album = json.loads(album_data)
    except (json.JSONDecodeError, ValueError):
        await update.message.reply_text(f"❌ 图包数据格式错误：{code}")
        return
    
    title = album.get("title", "未知标题")
    files_count = len(album.get("files", []))
    
    pending_deletes[uid] = code
    
    await update.message.reply_text(
        f"📋 图包信息预览：\n"
        f"序列码：{code}\n"
        f"标题：{title}\n"
        f"图片数：{files_count}\n\n"
        f"确定要删除《{title}》吗？(yes/no)"
    )

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    logger.info(f"[handle_confirmation] User {uid} in pending_deletes: {uid in pending_deletes}")
    
    if uid not in pending_deletes:
        logger.info(f"[handle_confirmation] User {uid} not in pending_deletes, skipping")
        return
    
    text = (update.message.text or "").strip().lower()
    
    logger.info(f"[handle_confirmation] Processing confirmation for user {uid}: '{text}'")
    
    if text not in ["yes", "no"]:
        logger.info(f"[handle_confirmation] Invalid confirmation text: '{text}', expecting 'yes' or 'no'")
        await update.message.reply_text("请回复 yes 或 no")
        return
    
    code = pending_deletes[uid]
    
    if text == "no":
        del pending_deletes[uid]
        logger.info(f"[handle_confirmation] User {uid} cancelled deletion of {code}")
        await update.message.reply_text(f"❌ 已取消删除图包 {code}")
        return
    
    if text == "yes":
        ok = kv_delete(code)
        if ok:
            del pending_deletes[uid]
            logger.info(f"[handle_confirmation] User {uid} successfully deleted {code}")
            await update.message.reply_text(f"✅ 已删除图包 {code}")
        else:
            del pending_deletes[uid]
            logger.info(f"[handle_confirmation] Failed to delete {code} for user {uid}")
            await update.message.reply_text(f"❌ 删除图包失败，请稍后重试：{code}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start_album", start_album))
    app.add_handler(CommandHandler("end_album", end_album))
    app.add_handler(CommandHandler("set_pass", set_pass))
    app.add_handler(CommandHandler("delete", delete_album))

    # MessageHandlers must be ordered from most specific to least specific
    # handle_confirmation only processes messages when user is in pending_deletes
    # handle_title processes messages starting with # when album exists
    # Other photo/document handlers must come after text handlers
    logger.info("[main] Registering message handlers in order: confirmation, title, photo, document")
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_title))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_confirmation))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("[main] Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
