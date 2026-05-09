"""
Social Media Handlers
Module for handling TikTok
"""

import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.Social_Media_Download.tiktok import download_tiktok
from Logic.utils.helpers import _delete_message_safely, _handle_download_error

from languages import get_text
from Logic.utils.Uploader import safe_upload

router = Router()

# ============================================================================
# TikTok Handler
# ============================================================================

@router.message(F.text.contains("tiktok.com"))
async def handle_tiktok(message: types.Message):
    """Handle TikTok video and carousel downloads."""
    lang = message.from_user.language_code or "en"
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        url = message.text.strip()
        print(f"[TikTok] Processing URL: {url}")

        # Download in separate thread
        result = await asyncio.to_thread(download_tiktok, url, verbose=True)

        # Delete status message
        await _delete_message_safely(status_msg)

        if result:
            path = result.get("path") if isinstance(result, dict) else result
            
            if path and os.path.exists(path):
                print(f"[TikTok] Upload starting for: {path}")
                
                # REMOVED: Button selection logic (lines 47-101)
                # Now directly uploads video/carousel without asking user
                await safe_upload(message, path, lang, caption=get_text("spoon", lang))
            else:
                await message.answer(get_text("no_media", lang))
        else:
            await message.answer(get_text("no_media", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)


# REMOVED: Entire callback_query handler (lines 114-205)
# No longer needed since we removed the button selection feature