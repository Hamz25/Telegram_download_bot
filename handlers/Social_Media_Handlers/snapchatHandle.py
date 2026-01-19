"""
Social Media Handlers
Module for handling TikTok, Snapchat, and Instagram downloads.
"""

import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.Social_Media_Download.snapchat import download_snapchat_video
from Logic.utils.helpers import _delete_message_safely, _handle_download_error

from languages import get_text
from Logic.utils.Uploader import safe_upload

router = Router()


@router.message(F.text.contains("snapchat.com"))
async def handle_snapchat(message: types.Message):
    """Handle Snapchat video downloads."""
    lang = message.from_user.language_code or "en"
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        url = message.text.strip()
        print(f"[Snapchat] Processing URL: {url}")

        path = await asyncio.to_thread(download_snapchat_video, url)

        await _delete_message_safely(status_msg)

        if path and os.path.exists(path):
            await safe_upload(message, path, lang, caption=get_text("snap_success", lang))
        else:
            await message.answer(get_text("no_media", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)
