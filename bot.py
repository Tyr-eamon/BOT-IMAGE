"""Telegram photo collection bot backed by Cloudflare KV storage."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ALBUM_STATE_KEY = "album_state"
ALBUM_SEQUENCE_KEY = "_album_sequence"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_NAMESPACE_ID = os.getenv("CF_NAMESPACE_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
WORKER_BASE_URL = (os.getenv("WORKER_BASE_URL") or "").rstrip("/")


class CloudflareKVClient:
    """Thin wrapper around the Cloudflare KV REST API."""

    def __init__(self, account_id: str, namespace_id: str, api_token: str) -> None:
        if not all([account_id, namespace_id, api_token]):
            raise ValueError("Missing Cloudflare KV configuration.")
        self.base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
            f"/storage/kv/namespaces/{namespace_id}"
        )
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def _values_url(self, key: str) -> str:
        return f"{self.base_url}/values/{key}"

    def get_value(self, key: str) -> Optional[str]:
        response = requests.get(self._values_url(key), headers=self.headers, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text

    def put_value(
        self, key: str, value: str, content_type: str = "text/plain"
    ) -> None:
        headers = {**self.headers, "Content-Type": content_type}
        response = requests.put(
            self._values_url(key), headers=headers, data=value, timeout=10
        )
        response.raise_for_status()

    def _next_sequence_index(self) -> int:
        raw_value = self.get_value(ALBUM_SEQUENCE_KEY)
        try:
            current = int(raw_value) if raw_value is not None else 0
        except ValueError:
            logger.warning(
                "Invalid sequence value '%s' detected, resetting counter to 0", raw_value
            )
            current = 0
        return current + 1

    def save_album(self, payload: Dict[str, List[str]]) -> str:
        next_index = self._next_sequence_index()
        album_code = f"a{next_index:02d}"
        self.put_value(
            album_code,
            json.dumps(payload, ensure_ascii=False),
            content_type="application/json",
        )
        self.put_value(ALBUM_SEQUENCE_KEY, str(next_index))
        return album_code


def get_kv_client() -> CloudflareKVClient:
    return CloudflareKVClient(CF_ACCOUNT_ID, CF_NAMESPACE_ID, CF_API_TOKEN)


def _ensure_message(update: Update):
    message = update.effective_message
    if message is None:
        raise ValueError("Update does not contain a message context")
    return message


def _get_user_session(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    return context.user_data.get(ALBUM_STATE_KEY)


def _create_user_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ALBUM_STATE_KEY] = {"title": None, "files": []}


def _clear_user_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(ALBUM_STATE_KEY, None)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = _ensure_message(update)
    welcome_message = (
        "🤖 Welcome to the Photo Collection Bot!\n\n"
        "Collect Telegram photos into Cloudflare KV-backed albums.\n\n"
        "Available commands:\n"
        "/start - Display this help message\n"
        "/start_album - Begin recording a new album\n"
        "/end_album - Save the active album to storage\n\n"
        "Workflow:\n"
        "1️⃣ Use /start_album\n"
        "2️⃣ Send a message starting with # to set the album title\n"
        "3️⃣ Send photos to collect their file_ids\n"
        "4️⃣ Finish with /end_album"
    )
    await message.reply_text(welcome_message)


async def start_album_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = _ensure_message(update)
    if _get_user_session(context):
        await message.reply_text(
            "⚠️ You already have an active album. Use /end_album to finish it first."
        )
        return
    _create_user_session(context)
    await message.reply_text(
        "📸 Album session started!\n"
        "Send a title message beginning with # (e.g. #My Album) and then upload photos."
    )


async def end_album_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = _ensure_message(update)
    session = _get_user_session(context)
    if not session:
        await message.reply_text("❌ No active album. Use /start_album to begin.")
        return
    if not session.get("title"):
        await message.reply_text(
            "⚠️ Please set an album title first by sending a message that starts with #."
        )
        return
    files = session.get("files", [])
    if not files:
        await message.reply_text("⚠️ Add at least one photo before ending the album.")
        return

    await message.reply_text("💾 Saving album to Cloudflare KV...")

    payload = {"title": session["title"], "files": list(files)}

    try:
        album_code = await asyncio.to_thread(
            context.bot_data["kv_client"].save_album, payload
        )
    except (requests.RequestException, ValueError) as exc:
        logger.exception("Failed to save album")
        await message.reply_text(
            "❌ Could not save the album. Please try again later."
        )
        return

    _clear_user_session(context)

    response = (
        f"✅ Album saved successfully!\n"
        f"Code: {album_code}\n"
        f"Title: {payload['title']}\n"
        f"Photos stored: {len(payload['files'])}"
    )
    if WORKER_BASE_URL:
        response += f"\nShare link: {WORKER_BASE_URL}/{album_code}"

    await message.reply_text(response)


async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = _ensure_message(update)
    session = _get_user_session(context)
    if not session:
        return

    text = (message.text or "").strip()
    if not text.startswith("#"):
        return

    title = text.lstrip("#").strip()
    if not title:
        await message.reply_text("❌ Title cannot be empty. Try again with #Your Title.")
        return

    session["title"] = title
    await message.reply_text(
        f"✅ Title set to: {title}. Now send photos to populate the album."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = _ensure_message(update)
    session = _get_user_session(context)
    if not session:
        await message.reply_text("ℹ️ Start an album first with /start_album.")
        return
    if not session.get("title"):
        await message.reply_text(
            "⚠️ Set a title before uploading photos by sending a message starting with #."
        )
        return

    if not message.photo:
        await message.reply_text("⚠️ Unable to read the photo payload. Please resend the image.")
        return

    largest_photo = max(
        message.photo, key=lambda p: p.file_size or 0  # pick the best quality variant
    )
    session.setdefault("files", []).append(largest_photo.file_id)
    await message.reply_text(
        f"📷 Photo added! Total photos in album: {len(session['files'])}."
    )


async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error while processing update: %s", context.error)


def build_application() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is required.")
    if not all([CF_ACCOUNT_ID, CF_NAMESPACE_ID, CF_API_TOKEN]):
        raise RuntimeError("Cloudflare KV environment variables are required.")
    kv_client = get_kv_client()
    application = Application.builder().token(BOT_TOKEN).build()
    application.bot_data["kv_client"] = kv_client

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("start_album", start_album_command))
    application.add_handler(CommandHandler("end_album", end_album_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)
    )
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    application = build_application()
    logger.info("Starting long polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
