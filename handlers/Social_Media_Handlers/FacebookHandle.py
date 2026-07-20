"""
Social Media Handlers
Module for handling Facebook
"""

import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.Social_Media_Download.facebook import download_facebook
from Logic.utils.helpers import _delete_message_safely, _handle_download_error

from languages import get_text
from Logic.utils.Uploader import safe_upload

router = Router()

# ============================================================================
# Facebook Handler
# ============================================================================

FACEBOOK_URL_REGEXP = r"(https?://)?(www\.|m\.|web\.)?(facebook\.com|fb\.watch)/\S+"


@router.message(F.text.regexp(FACEBOOK_URL_REGEXP))
async def handle_facebook(message: types.Message):
    """Handle Facebook video/reel and photo post downloads."""
    lang = message.from_user.language_code or "en"
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        url = message.text.strip()
        print(f"[Facebook] Processing URL: {url}")

        # Download in separate thread
        result = await asyncio.to_thread(download_facebook, url, verbose=True)

        # Delete status message
        await _delete_message_safely(status_msg)

        if result:
            path = result.get("path") if isinstance(result, dict) else result

            if path and os.path.exists(path):
                print(f"[Facebook] Upload starting for: {path}")
                await safe_upload(message, path, lang, caption=get_text("spoon", lang))
            else:
                await message.answer(get_text("no_media", lang))
        else:
            await message.answer(get_text("no_media", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)
