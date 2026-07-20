"""
Social Media Handlers
Module for handling X (Twitter)
"""

import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.Social_Media_Download.x import download_x
from Logic.utils.helpers import _delete_message_safely, _handle_download_error

from languages import get_text
from Logic.utils.Uploader import safe_upload

router = Router()

# ============================================================================
# X (Twitter) Handler
# ============================================================================

X_URL_REGEXP = r"(https?://)?(www\.)?(x\.com|twitter\.com|mobile\.twitter\.com|t\.co)/\S+"


@router.message(F.text.regexp(X_URL_REGEXP))
async def handle_x(message: types.Message):
    """Handle X (Twitter) video and photo post downloads."""
    lang = message.from_user.language_code or "en"
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        url = message.text.strip()
        print(f"[X] Processing URL: {url}")

        # Download in separate thread
        result = await asyncio.to_thread(download_x, url, verbose=True)

        # Delete status message
        await _delete_message_safely(status_msg)

        if result:
            path = result.get("path") if isinstance(result, dict) else result

            if path and os.path.exists(path):
                print(f"[X] Upload starting for: {path}")
                await safe_upload(message, path, lang, caption=get_text("spoon", lang))
            else:
                await message.answer(get_text("no_media", lang))
        else:
            await message.answer(get_text("no_media", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)
