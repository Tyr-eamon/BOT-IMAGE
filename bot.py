import os
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters, CallbackQueryHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 你的 Telegram ID
OWNER_ID = 8040798522  
ALLOWED_USERS = set([OWNER_ID])

BOT_TOKEN = os.environ["BOT_TOKEN"]
CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_NAMESPACE_ID = os.environ["CF_NAMESPACE_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]
WORKER_BASE_URL = os.getenv("WORKER_BASE_URL", "https://example.workers.dev")

# 自定义分类 (需与 Worker 端保持一致)
CATEGORIES = [
    "Popular Cosplay",
    "Video Cosplay",
    "Explore Categories",
    "Best Cosplayer",
    "Level Cosplay",
    "Top Cosplay"
]

current_albums = {}
pending_deletes = {}
COUNTER_KEY = "__counter"

# ---------- 权限 ----------
def is_allowed(uid: int) -> bool:
    return uid == OWNER_ID or uid in ALLOWED_USERS

async def ensure_allowed(update: Update):
    uid = update.effective_user.id
    if not is_allowed(uid):
        await update.message.reply_text("❌ 无权使用。")
        return False
    return True

# ---------- KV ----------
def kv_headers():
    return {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "text/plain"}

def kv_put(key: str, value: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{key}"
    resp = requests.put(url, headers=kv_headers(), data=value.encode("utf-8"))
    return resp.status_code == 200

def kv_get(key: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{key}"
    resp = requests.get(url, headers=kv_headers())
    return resp.text if resp.status_code == 200 else None

def kv_delete(key: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{key}"
    resp = requests.delete(url, headers=kv_headers())
    return resp.status_code in (200, 204)

def next_code() -> str:
    cur = kv_get(COUNTER_KEY)
    n = int(cur) + 1 if cur else 1
    kv_put(COUNTER_KEY, str(n))
    return f"a0{n}" if n < 10 else f"a{n}"

# ---------- Bot Logic ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    await update.message.reply_text(
        "📸 **MTCweb Bot**\n\n"
        "1️⃣ /start_album - 开始\n"
        "2️⃣ 发送 `#标题` - 设置标题并选择分类\n"
        "3️⃣ 发送图片/文件\n"
        "4️⃣ /end_album - 完成\n"
    )

async def start_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    current_albums[uid] = {
        "title": None,
        "category": CATEGORIES[2], # 默认值 "Explore Categories"
        "files": [],
        "attachments": [],
        "zip": None,
        "password": None,
    }
    await update.message.reply_text("🟦 新图包已开始。\n请发送标题（以 # 开头），例如：`#Arty Genshin`", parse_mode="Markdown")

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    text = update.message.text.strip()
    album = current_albums.get(uid)

    if not album:
        if text.startswith("#"): await update.message.reply_text("请先 /start_album")
        return

    if not text.startswith("#"): return

    # 1. 保存标题
    album["title"] = text[1:].strip()

    # 2. 构建分类选择键盘
    keyboard = []
    # 每行放2个按钮
    for i in range(0, len(CATEGORIES), 2):
        row = []
        row.append(InlineKeyboardButton(CATEGORIES[i], callback_data=f"cat_{i}"))
        if i + 1 < len(CATEGORIES):
            row.append(InlineKeyboardButton(CATEGORIES[i+1], callback_data=f"cat_{i+1}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"✅ 标题已设为：{album['title']}\n\n👇 **请选择分类：**", reply_markup=reply_markup)

async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    uid = query.from_user.id
    data = query.data
    
    if not data.startswith("cat_"): return
    
    idx = int(data.split("_")[1])
    selected_cat = CATEGORIES[idx]
    
    if uid in current_albums:
        current_albums[uid]["category"] = selected_cat
        await query.edit_message_text(f"✅ 标题：{current_albums[uid]['title']}\n✅ 分类：**{selected_cat}**\n\n现在请发送图片或文件。")
    else:
        await query.edit_message_text("❌ 会话已过期，请重新开始。")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    if uid in current_albums:
        current_albums[uid]["files"].append(update.message.photo[-1].file_id)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album: return

    doc = update.message.document
    file_info = {"file_id": doc.file_id, "file_name": doc.file_name or "file", "mime_type": doc.mime_type}
    album["attachments"].append(file_info)
    
    lname = doc.file_name.lower() if doc.file_name else ""
    if not album["zip"] and (lname.endswith(".zip") or lname.endswith(".rar") or lname.endswith(".7z")):
        album["zip"] = file_info
        await update.message.reply_text(f"🎁 识别为压缩包：{doc.file_name}")

async def end_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    album = current_albums.get(uid)
    
    if not album: return await update.message.reply_text("未开始新图包")
    if not album["files"]: return await update.message.reply_text("未发送图片")

    code = next_code()
    kv_put(code, json.dumps(album, ensure_ascii=False))
    del current_albums[uid]
    
    await update.message.reply_text(f"🎉 发布成功！\nCode: `{code}`\nLink: {WORKER_BASE_URL}/{code}", parse_mode="Markdown")

async def delete_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    try:
        code = update.message.text.split()[1]
        pending_deletes[update.effective_user.id] = code
        await update.message.reply_text(f"确认删除 {code}？回复 yes")
    except:
        await update.message.reply_text("用法：/delete a01")

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in pending_deletes and update.message.text.lower() == "yes":
        code = pending_deletes.pop(uid)
        kv_delete(code)
        await update.message.reply_text(f"已删除 {code}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_album", start_album))
    app.add_handler(CommandHandler("end_album", end_album))
    app.add_handler(CommandHandler("delete", delete_album))
    
    app.add_handler(MessageHandler(filters.Regex(r"^#"), handle_title))
    app.add_handler(CallbackQueryHandler(handle_category_callback))
    
    app.add_handler(MessageHandler(filters.Regex(r"^(?i)yes$"), handle_confirm))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
