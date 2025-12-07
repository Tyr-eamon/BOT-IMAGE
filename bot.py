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

# --- 配置区 ---
OWNER_ID = 8040798522 
ALLOWED_USERS = set([OWNER_ID])

BOT_TOKEN = os.environ["BOT_TOKEN"]
CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_NAMESPACE_ID = os.environ["CF_NAMESPACE_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]
WORKER_BASE_URL = os.getenv("WORKER_BASE_URL", "https://example.workers.dev")

DEFAULT_CATS = "Popular Cosplay,Video Cosplay,Explore Categories,Best Cosplayer,Level Cosplay,Top Cosplay"
raw_cats = os.getenv("CATEGORIES", DEFAULT_CATS)
CATEGORIES = [c.strip() for c in raw_cats.split(",") if c.strip()]

current_albums = {}
COUNTER_KEY = "__counter"

# --- 辅助函数 (权限/KV) ---
async def ensure_allowed(update: Update):
    uid = update.effective_user.id
    if uid != OWNER_ID and uid not in ALLOWED_USERS:
        await update.message.reply_text("❌ 无权使用。")
        return False
    return True

def kv_headers(): return {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "text/plain"}
def kv_base(): return f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}"
def kv_put(key, value): return requests.put(f"{kv_base()}/values/{key}", headers=kv_headers(), data=value.encode("utf-8")).status_code == 200
def kv_get(key): 
    r = requests.get(f"{kv_base()}/values/{key}", headers=kv_headers())
    return r.text if r.status_code == 200 else None
def next_code():
    cur = kv_get(COUNTER_KEY)
    n = int(cur) + 1 if cur else 1
    kv_put(COUNTER_KEY, str(n))
    return f"a0{n}" if n < 10 else f"a{n}"

# --- 核心逻辑 ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    await update.message.reply_text(
        "📸 **Bot Ready**\n"
        "1. /start_album - 开始新图包\n"
        "2. 直接发送文本 - 设置标题\n"
        "3. /nav - 选择分类\n"
        "4. 发送图片/文件\n"
        "5. /end_album - 发布"
    )

async def start_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    # 初始化，默认分类为列表第一个
    default_cat = CATEGORIES[0] if CATEGORIES else ""
    current_albums[update.effective_user.id] = {
        "title": "未命名图包", 
        "category": default_cat, 
        "files": [], "attachments": [], "zip": None, "password": None
    }
    await update.message.reply_text(f"🟦 已开始！\n默认分类：**{default_cat}**\n\n请直接发送图包标题。")

async def handle_text_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 处理普通文本消息 -> 设置标题
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    text = update.message.text.strip()
    album = current_albums.get(uid)
    
    if not album: 
        # 如果没开始图包，忽略普通文本，或者提示
        return 

    album["title"] = text
    await update.message.reply_text(f"✅ 标题已更新：**{text}**\n\n发送 /nav 修改分类，或直接发图。")

async def handle_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 处理 /nav 命令 -> 弹出分类选择
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album: return await update.message.reply_text("请先 /start_album")

    # 生成按钮
    keyboard = []
    for i in range(0, len(CATEGORIES), 2):
        row = [InlineKeyboardButton(CATEGORIES[i], callback_data=f"cat_{i}")]
        if i + 1 < len(CATEGORIES):
            row.append(InlineKeyboardButton(CATEGORIES[i+1], callback_data=f"cat_{i+1}"))
        keyboard.append(row)
    
    await update.message.reply_text(f"👇 **当前分类：{album['category']}**\n请选择新分类：", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid not in current_albums: return await query.edit_message_text("❌ 会话过期")
    
    idx = int(query.data.split("_")[1])
    cat = CATEGORIES[idx]
    current_albums[uid]["category"] = cat
    await query.edit_message_text(f"✅ 分类已更新：**{cat}**")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album: return
    
    if update.message.photo:
        album["files"].append(update.message.photo[-1].file_id)
    elif update.message.document:
        doc = update.message.document
        info = {"file_id": doc.file_id, "file_name": doc.file_name, "mime_type": doc.mime_type}
        album["attachments"].append(info)
        if not album["zip"] and doc.file_name.lower().endswith((".zip", ".rar", ".7z")):
            album["zip"] = info
            await update.message.reply_text(f"🎁 Zip: {doc.file_name}")

async def end_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_allowed(update): return
    uid = update.effective_user.id
    album = current_albums.get(uid)
    if not album or not album["files"]: return await update.message.reply_text("❌ 数据为空或未上传图片")
    
    code = next_code()
    if kv_put(code, json.dumps(album, ensure_ascii=False)):
        del current_albums[uid]
        await update.message.reply_text(f"🎉 发布成功！\nCode: `{code}`\n标题: {album['title']}\n分类: {album['category']}\nLink: {WORKER_BASE_URL}/{code}")
    else:
        await update.message.reply_text("❌ 写入失败")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_album", start_album))
    app.add_handler(CommandHandler("nav", handle_nav))     # 新增：/nav 触发选择
    app.add_handler(CommandHandler("end_album", end_album))
    
    app.add_handler(CallbackQueryHandler(handle_category_callback))
    
    # 普通文本消息 -> 设置标题 (不再需要 # 号)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_title))
    
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))
    
    logger.info("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
