"""
Social Media Handlers
Module for handling TikTok
"""

import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
                
                is_video = path.lower().endswith(('.mp4', '.mov', '.webm', '.avi'))
                
                if is_video:
                    # Find thumbnail
                    thumbnail_path = None
                    base_name = os.path.splitext(path)[0]
                    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        thumb = base_name + ext
                        if os.path.exists(thumb):
                            thumbnail_path = thumb
                            break
                    
                    if thumbnail_path:
                        # Build download options keyboard
                        builder = InlineKeyboardBuilder()
                        builder.button(
                            text=get_text("btn_video", lang), 
                            callback_data=f"tiktok_video_{message.message_id}"
                        )
                        builder.button(
                            text=get_text("btn_audio", lang), 
                            callback_data=f"tiktok_audio_{message.message_id}"
                        )
                        builder.button(
                            text=get_text("btn_voice", lang), 
                            callback_data=f"tiktok_voice_{message.message_id}"
                        )
                        builder.adjust(3)
                        
                        # Store download data
                        if not hasattr(message.bot, '_download_data'):
                            message.bot._download_data = {}
                        
                        storage_key = f"tiktok_{message.message_id}"
                        message.bot._download_data[storage_key] = {
                            "video_path": path,
                            "url": url,
                            "user_id": message.from_user.id,
                            "lang": lang
                        }
                        
                        # Send thumbnail with buttons
                        try:
                            from aiogram.types import FSInputFile
                            await message.answer_photo(
                                photo=FSInputFile(thumbnail_path),
                                caption=get_text("choose_format", lang),
                                reply_markup=builder.as_markup()
                            )
                        except Exception as e:
                            print(f"[TikTok] Failed to send thumbnail: {e}")
                            await safe_upload(message, path, lang, caption=get_text("tiktok_success", lang))
                    else:
                        # No thumbnail, just upload
                        await safe_upload(message, path, lang, caption=get_text("tiktok_success", lang))
                else:
                    # Carousel (photos)
                    await safe_upload(message, path, lang, caption=get_text("tiktok_success", lang))
            else:
                await message.answer(get_text("no_media", lang))
        else:
            await message.answer(get_text("no_media", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)


@router.callback_query(F.data.startswith("tiktok_"))
async def process_tiktok_download(callback: types.CallbackQuery):
    """
    Process TikTok download option selection.
    
    FIXED: Now properly deletes button message after selection.
    """
    lang = callback.from_user.language_code or "en"
    parts = callback.data.split("_", 2)
    
    if len(parts) < 3:
        await callback.answer(get_text("error_invalid", lang), show_alert=True)
        return
    
    download_type = parts[1]  # video, audio, voice
    message_id = parts[2]
    
    await callback.answer()  # Acknowledge button press
    
    # FIXED: Delete button message immediately
    await _delete_message_safely(callback.message)
    
    # Retrieve stored data
    if not hasattr(callback.bot, '_download_data'):
        await callback.message.answer(get_text("error_session", lang))
        return
    
    storage_key = f"tiktok_{message_id}"
    tiktok_data = callback.bot._download_data.get(storage_key)
    
    if not tiktok_data:
        await callback.message.answer(get_text("error_session", lang))
        return
    
    video_path = tiktok_data.get("video_path")
    url = tiktok_data.get("url")
    user_lang = tiktok_data.get("lang", lang)
    
    # Show processing status
    status_msg = await callback.message.answer(get_text("uploading", user_lang))
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)
    
    try:
        if download_type == "video":
            await safe_upload(
                callback.message,
                video_path,
                user_lang,
                caption=get_text("tiktok_success", user_lang)
            )
        
        elif download_type in ["audio", "voice"]:
            # Extract audio using yt-dlp
            from Logic.yt import download_youtube
            
            audio_result = await asyncio.to_thread(
                download_youtube, url, quality="720", is_audio=True
            )
            
            if audio_result and audio_result.get("path"):
                if download_type == "audio":
                    await safe_upload(
                        callback.message,
                        audio_result["path"],
                        user_lang,
                        media_type="audio",
                        caption=get_text("tiktok_audio", user_lang),
                        title=audio_result.get("title", "TikTok"),
                        performer=audio_result.get("performer", "TikTok"),
                    )
                else:
                    # Voice message
                    from aiogram.types import FSInputFile
                    await callback.message.answer_voice(
                        voice=FSInputFile(audio_result["path"]),
                        caption=get_text("tiktok_voice", user_lang)
                    )
            else:
                await callback.message.answer(get_text("error_audio", user_lang))
        
        # Delete status message
        await _delete_message_safely(status_msg)
        
        print(f"[TikTok] Downloaded as {download_type}")
    
    except Exception as e:
        await _handle_download_error(callback, user_lang, e, status_msg)
    
    finally:
        # Clean up stored data
        if hasattr(callback.bot, '_download_data'):
            callback.bot._download_data.pop(storage_key, None)