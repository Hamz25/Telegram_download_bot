"""
YouTube Download Handler
Module for handling YouTube videos and shorts with quality selection.
Supports both video and audio downloads with quality options.
"""

import asyncio
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder

from Logic.Social_Media_Download.yt import get_video_info, download_youtube
from languages import get_text
from Logic.utils.Uploader import safe_upload


# Router initialization
router = Router()

# ============================================================================
# Helper Functions
# ============================================================================


def _format_video_duration(duration: int) -> str:
    """
    Format duration in seconds to MM:SS format.
    
    Args:
        duration: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if not duration:
        return "Unknown"
    return f"{duration // 60}:{duration % 60:02d}"


def _format_file_size(size: int) -> str:
    """
    Format file size in bytes to MB format.
    
    Args:
        size: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if not size:
        return "Unknown"
    return f"{size / (1024**2):.1f}MB"


# ============================================================================
# YouTube URL Handler
# ============================================================================

@router.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_youtube(message: types.Message, state: FSMContext):
    """
    Handle YouTube video and shorts URLs.
    
    Behavior:
    - YouTube Shorts: Download immediately in best quality
    - Regular Videos: Show quality selection menu
    
    Supported qualities: 360p, 720p, 1080p, MP3 (audio)
    """
    from index import BotStates  # Local import to avoid circular dependency

    lang = message.from_user.language_code or "en"

    try:
        url = message.text.strip()
        print(f"[YouTube] Processing URL: {url}")

        # Fetch video information
        (
            info,
            is_short,
            size,
            title,
            thumbnail,
            duration,
        ) = await asyncio.to_thread(get_video_info, url)

        if not info:
            await message.answer(
                get_text("error_general", lang).format(
                    e="Failed to fetch video info"
                )
            )
            return

        if is_short:
            # YouTube Short - download immediately in best quality
            await _handle_youtube_short(message, url, title, lang)

        else:
            # Regular video - show quality selection
            await _handle_video_quality_selection(
                message, state, url, title, duration, size, thumbnail, lang
            )

    except Exception as e:
        print(f"[YouTube] Handler error: {e}")
        import traceback

        traceback.print_exc()
        await message.answer(
            get_text("error_general", lang).format(e=str(e))
        )


# ============================================================================
# YouTube Short Handler with Cleanup
# ============================================================================


async def _handle_youtube_short(
    message: types.Message, url: str, title: str, lang: str
):
    """
    Handle YouTube Shorts download.
    
    Downloads in best available quality and sends thumbnail with download options.
    
    Args:
        message: User message object
        url: YouTube short URL
        title: Video title
        lang: User language code
    """
    from index import BotStates

    status = await message.answer(get_text("shorts_detected", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        result = await asyncio.to_thread(
            download_youtube, url, quality="720", is_audio=False
        )

        await status.delete()

        if result and result.get("path"):
            video_path = result["path"]
            
            # Find thumbnail
            thumbnail_path = None
            base_name = os.path.splitext(video_path)[0]
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                thumb = base_name + ext
                if os.path.exists(thumb):
                    thumbnail_path = thumb
                    break
            
            # Build download options keyboard
            builder = InlineKeyboardBuilder()
            builder.button(
                text=get_text("btn_video", lang), 
                callback_data=f"short_video_{message.message_id}"
            )
            builder.button(
                text=get_text("btn_audio", lang), 
                callback_data=f"short_audio_{message.message_id}"
            )
            builder.button(
                text=get_text("btn_voice", lang), 
                callback_data=f"short_voice_{message.message_id}"
            )
            builder.adjust(3)
            
            # Store download data using bot object
            storage_key = f"short_{message.message_id}"
            
            if not hasattr(message.bot, '_download_data'):
                message.bot._download_data = {}
            
            message.bot._download_data[storage_key] = {
                "video_path": video_path,
                "title": title,
                "url": url,
                "lang": lang,
            }
            
            # Send thumbnail with buttons
            if thumbnail_path:
                try:
                    from aiogram.types import FSInputFile
                    await message.answer_photo(
                        photo=FSInputFile(thumbnail_path),
                        caption=get_text("choose_format", lang),
                        reply_markup=builder.as_markup()
                    )
                except Exception as e:
                    print(f"[YouTube] Failed to send thumbnail: {e}")
                    await safe_upload(
                        message,
                        video_path,
                        lang,
                        media_type="video",
                        caption=f"✅ {title}",
                    )
            else:
                await safe_upload(
                    message,
                    video_path,
                    lang,
                    media_type="video",
                    caption=f"✅ {title}",
                )
        else:
            await message.answer(
                get_text("error_general", lang).format(e="Download failed")
            )

    except Exception as e:
        print(f"[YouTube] Short download error: {e}")
        await message.answer(
            get_text("error_general", lang).format(e=str(e))
        )


# ============================================================================
# Video Quality Selection
# ============================================================================


async def _handle_video_quality_selection(
    message: types.Message,
    state: FSMContext,
    url: str,
    title: str,
    duration: int,
    size: int,
    thumbnail: str,
    lang: str,
):
    """
    Show quality selection menu for regular YouTube videos.
    
    Offers: 360p, 720p, 1080p, MP3 (audio)
    
    Args:
        message: User message object
        state: FSM context
        url: YouTube video URL
        title: Video title
        duration: Video duration in seconds
        size: Estimated file size in bytes
        thumbnail: Thumbnail URL
        lang: User language code
    """
    from index import BotStates

    await state.update_data(yt_url=url, yt_title=title)

    # Build quality selection keyboard
    builder = InlineKeyboardBuilder()

    # Add quality options
    for quality in ["360", "720", "1080"]:
        builder.button(text=f"🎬 {quality}p", callback_data=f"q_{quality}")

    # Add audio option
    builder.button(text="🎵 MP3", callback_data="q_audio")

    builder.adjust(2)  # 2 buttons per row

    # Format video info message
    duration_str = _format_video_duration(duration)
    size_str = _format_file_size(size)

    info_msg = (
        f"📺 <b>{title}</b>\n\n"
        f"⏱ <b>Duration:</b> {duration_str}\n"
        f"📦 <b>Size:</b> ~{size_str}\n\n"
        f"{get_text('video_found', lang)}"
    )

    # Send thumbnail if available
    if thumbnail:
        try:
            await message.answer_photo(
                photo=thumbnail,
                caption=info_msg,
                reply_markup=builder.as_markup(),
            )
        except Exception:
            # Fallback to text if thumbnail fails
            await message.answer(
                info_msg, reply_markup=builder.as_markup()
            )
    else:
        await message.answer(
            info_msg, reply_markup=builder.as_markup()
        )

    await state.set_state(BotStates.choosing_quality)


# ============================================================================
# Quality Selection Handler with Cleanup
# ============================================================================

@router.callback_query(F.data.startswith("q_"))
async def process_youtube_quality(
    callback: types.CallbackQuery, state: FSMContext
):
    """
    Process YouTube quality selection and download with cleanup.
    
    Handles:
    - Video downloads (360p, 720p, 1080p)
    - Audio downloads (MP3)
    """
    from index import botname  # Local import

    lang = callback.from_user.language_code or "en"
    choice = callback.data.split("_", 1)[1]

    # Get stored video data
    data = await state.get_data()
    url = data.get("yt_url")
    title = data.get("yt_title", "Video")

    if not url:
        await callback.answer(get_text("error_session", lang), show_alert=True)
        await state.clear()
        return

    await callback.answer()  # Acknowledge button press
    
    # Delete the quality selection message
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Send download status as a new message
    status_msg = await callback.message.answer(
        get_text("uploading", lang)
    )
    await callback.bot.send_chat_action(
        callback.message.chat.id, ChatAction.UPLOAD_VIDEO
    )

    try:
        is_audio = choice == "audio"

        print(
            f"[YouTube] Downloading: {url} "
            f"(Quality: {choice}, Audio: {is_audio})"
        )

        # Download video/audio
        result = await asyncio.to_thread(
            download_youtube, url, quality=choice, is_audio=is_audio
        )

        await status_msg.delete()

        if not result:
            await callback.message.answer(
                get_text("error_general", lang).format(e="Download failed")
            )
            await state.clear()
            return

        # Upload result
        if is_audio:
            # Audio file with metadata
            await safe_upload(
                callback.message,
                result["path"],
                lang,
                media_type="audio",
                caption=botname,
                title=result.get("title"),
                performer=result.get("performer"),
                thumbnail_url=result.get("thumb"),
            )
        else:
            # Video file
            await safe_upload(
                callback.message,
                result["path"],
                lang,
                media_type="video",
                caption=f"✅ {title}",
            )

        print(f"[YouTube] Successfully uploaded: {title}")

    except Exception as e:
        print(f"[YouTube] Download error: {e}")
        import traceback

        traceback.print_exc()

        try:
            await status_msg.delete()
        except Exception:
            pass

        await callback.message.answer(
            get_text("error_general", lang).format(e=str(e))
        )

    finally:
        await state.clear()


# ============================================================================
# Shorts Download Options with Cleanup
# ============================================================================


@router.callback_query(F.data.startswith("short_"))
async def process_short_download(callback: types.CallbackQuery):
    """
    Process YouTube Shorts download option selection with cleanup.
    
    Handles: video, audio, voice message downloads
    Deletes the button message after selection
    """
    from index import botname

    lang = callback.from_user.language_code or "en"
    parts = callback.data.split("_", 2)
    
    if len(parts) < 3:
        await callback.answer(get_text("error_invalid", lang), show_alert=True)
        return
    
    download_type = parts[1]  # video, audio, voice
    message_id = parts[2]
    
    await callback.answer()  # Acknowledge button press
    
    # Delete the button message
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    # Retrieve stored data
    if not hasattr(callback.bot, '_download_data'):
        await callback.message.answer(get_text("error_session", lang))
        return
    
    storage_key = f"short_{message_id}"
    short_data = callback.bot._download_data.get(storage_key)
    
    if not short_data:
        await callback.message.answer(get_text("error_session", lang))
        return
    
    video_path = short_data.get("video_path")
    title = short_data.get("title", "Video")
    url = short_data.get("url")
    user_lang = short_data.get("lang", lang)
    
    status_msg = await callback.message.answer(get_text("uploading", user_lang))
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)
    
    try:
        if download_type == "video":
            # Send as video
            await safe_upload(
                callback.message,
                video_path,
                user_lang,
                media_type="video",
                caption=f"✅ {title}"
            )
        
        elif download_type == "audio":
            # Convert to audio and send as MP3
            audio_result = await asyncio.to_thread(
                download_youtube, url, quality="720", is_audio=True
            )
            
            if audio_result and audio_result.get("path"):
                await safe_upload(
                    callback.message,
                    audio_result["path"],
                    user_lang,
                    media_type="audio",
                    caption=botname,
                    title=audio_result.get("title"),
                    performer=audio_result.get("performer"),
                )
            else:
                await callback.message.answer(
                    get_text("error_audio", user_lang)
                )
        
        elif download_type == "voice":
            # Convert to voice message
            audio_result = await asyncio.to_thread(
                download_youtube, url, quality="720", is_audio=True
            )
            
            if audio_result and audio_result.get("path"):
                from aiogram.types import FSInputFile
                
                audio_path = audio_result["path"]
                await callback.message.answer_voice(
                    voice=FSInputFile(audio_path),
                    caption=f"🎤 {title}"
                )
            else:
                await callback.message.answer(
                    get_text("error_audio", user_lang)
                )
        
        print(f"[YouTube] Short downloaded as {download_type}: {title}")
    
    except Exception as e:
        print(f"[YouTube] Short download error: {e}")
        import traceback
        traceback.print_exc()
        
        await callback.message.answer(
            get_text("error_general", user_lang).format(e=str(e))
        )
    
    finally:
        # Clean up stored data
        if hasattr(callback.bot, '_download_data'):
            callback.bot._download_data.pop(storage_key, None)
        try:
            await status_msg.delete()
        except Exception:
            pass