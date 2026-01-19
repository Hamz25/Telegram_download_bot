"""
Spotify Download Handler
Module for handling Spotify track downloads from direct URLs.
Converts Spotify tracks to audio format for Telegram upload.
"""

import asyncio
import logging
from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.Social_Media_Download.spotify import download_spotify_track
from languages import get_text
from Logic.utils.Uploader import safe_upload

# Configure logging
logger = logging.getLogger(__name__)

# Router initialization
router = Router()

# ============================================================================
# Spotify URL Handler
# ============================================================================


@router.message(F.text.contains("spotify.com"))
async def handle_spotify(message: types.Message):
    """
    Handle Spotify track downloads.

    Downloads audio from Spotify URLs and uploads to Telegram.
    Supports individual track links (open.spotify.com/track/...).

    Metadata included:
    - Track title
    - Artist/performer name
    """
    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(
        message.chat.id, ChatAction.UPLOAD_VOICE
    )

    try:
        print(f"[Spotify] Processing URL: {message.text}")

        # Download track in separate thread
        result = await asyncio.to_thread(
            download_spotify_track, message.text
        )

        await status_msg.delete()

        if result and result.get("path"):
            print(f"[Spotify] Upload starting: {result.get('title')}")
            
            await safe_upload(
                message,
                path=result["path"],
                lang=lang,
                media_type="audio",
                title=result.get("title"),
                performer=result.get("performer"),
            )
        else:
            await message.answer(get_text("no_media", lang))

    except Exception as e:
        print(f"[Spotify] Error: {e}")
        logger.error(f"Spotify download error: {e}")

        try:
            await status_msg.delete()
        except Exception:
            pass

        await message.answer(
            get_text("error_general", lang).format(e=str(e))
        )