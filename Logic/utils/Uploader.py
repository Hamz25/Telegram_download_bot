"""
File Uploader Module
Handles uploading media files to Telegram with proper error handling and cleanup.
"""

import os
import glob
import asyncio
from pathlib import Path
from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from languages import get_text
from Logic.utils.cleanUp import cleanup 

# Telegram Bot API limits
MAX_CHUNK_SIZE = 45 * 1024 * 1024  # 45MB per media group
MAX_SINGLE_FILE = 50 * 1024 * 1024 # 50MB per file
MAX_GROUP_SIZE = 10                 # Max 10 items per media group

async def safe_upload(
    message: types.Message, 
    path: str, 
    lang: str, 
    media_type: str = "video", 
    caption: str = None, 
    title: str = None, 
    performer: str = None, 
    thumbnail_url: str = None
):
    """
    Safely upload media to Telegram with proper error handling and cleanup.
    
    Args:
        message: Telegram message object
        path: File or directory path
        lang: Language code for error messages
        media_type: Type of media (video, audio, photo)
        caption: Optional caption for the media
        title: Title for audio files
        performer: Performer for audio files
        thumbnail_url: Thumbnail URL (deprecated, uses file-based thumbnails)
    """
    
    # Validate path exists
    if not path or not os.path.exists(path):
        await message.answer(get_text("error_file_not_found", lang))
        return
    
    # Determine cleanup target (entire downloads directory or parent folder)
    if os.path.isdir(path):
        folder_to_clean = path
    else:
        folder_to_clean = os.path.dirname(path)
    
    try:
        if os.path.isdir(path):
            # Upload multiple files from directory
            await _upload_directory(message, path, lang, caption)
        else:
            # Upload single file
            await _upload_single_file(message, path, lang, media_type, caption, title, performer)
    
    except Exception as e:
        print(f"[Uploader] Critical error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await message.answer(get_text("upload_failed", lang))
        except Exception:
            pass
    
    finally:
        # Schedule cleanup - FIXED: Ensure cleanup runs after all uploads complete
        print(f"[Uploader] Scheduling cleanup for: {folder_to_clean}")
        asyncio.create_task(_delayed_cleanup(folder_to_clean, delay=5))


async def _delayed_cleanup(path: str, delay: int):
    """
    Delayed cleanup to ensure all upload operations complete first.
    
    Args:
        path: Directory path to clean
        delay: Seconds to wait before cleanup
    """
    await asyncio.sleep(delay)
    await cleanup(path, delay=0)  # No additional delay needed


async def _upload_single_file(
    message: types.Message,
    file_path: str,
    lang: str,
    media_type: str,
    caption: str,
    title: str,
    performer: str
):
    """
    Upload a single media file with appropriate type handling.
    
    Handles file size validation and proper media type routing.
    """
    file_size = os.path.getsize(file_path)
    
    # Check file size limit
    if file_size > MAX_SINGLE_FILE:
        await message.answer(
            get_text("file_too_large", lang).format(
                size=round(file_size / (1024 * 1024), 2)
            )
        )
        return
    
    # Find thumbnail for videos
    thumbnail = _find_thumbnail(file_path) if media_type == "video" else None
    
    try:
        input_file = FSInputFile(file_path)
        
        if media_type == "audio":
            await message.answer_audio(
                input_file, 
                caption=caption, 
                title=title, 
                performer=performer,
                thumbnail=thumbnail
            )
        elif media_type == "video":
            await message.answer_video(
                input_file, 
                caption=caption,
                thumbnail=thumbnail
            )
        else:  # photo
            await message.answer_photo(input_file, caption=caption)
        
        print(f"[Uploader] ✅ Uploaded: {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"[Uploader] ❌ Failed to upload {file_path}: {e}")
        raise


async def _upload_directory(
    message: types.Message,
    directory: str,
    lang: str,
    caption: str
):
    """
    Upload all media files from a directory.
    
    Groups files into media groups where appropriate.
    Intelligently filters out thumbnails that belong to videos.
    """
    # Find all media files
    valid_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.m4v', '*.mp3']
    files = []
    
    for ext in valid_extensions:
        files.extend(glob.glob(os.path.join(directory, ext)))
        files.extend(glob.glob(os.path.join(directory, ext.upper())))
    
    # Remove duplicates and sort
    files = sorted(list(set(files)))
    
    if not files:
        await message.answer(get_text("no_media", lang))
        return
    
    print(f"[Uploader] Found {len(files)} total files in directory")
    
    # Separate files into categories and filter thumbnails
    audio_files = [f for f in files if f.lower().endswith('.mp3')]
    
    # For media files, filter out thumbnails
    media_files = []
    for f in files:
        if f.lower().endswith('.mp3'):
            continue  # Skip audio, handled separately
        
        # Skip if this file is a thumbnail
        if _is_thumbnail_file(f, files):
            continue
        
        media_files.append(f)
    
    print(f"[Uploader] After filtering: {len(media_files)} media files, {len(audio_files)} audio files")
    
    # Upload audio files individually (they can't be in media groups)
    for audio_file in audio_files:
        try:
            await _upload_single_file(
                message, 
                audio_file, 
                lang, 
                "audio", 
                caption, 
                None, 
                None
            )
            await asyncio.sleep(1)  # Anti-flood delay
        except Exception as e:
            print(f"[Uploader] Failed to upload audio {audio_file}: {e}")
    
    # Group and upload media files
    if media_files:
        await _upload_media_groups(message, media_files, lang, caption)


async def _upload_media_groups(
    message: types.Message,
    files: list,
    lang: str,
    caption: str
):
    """
    Upload media files in optimized groups.
    
    Handles both photos and videos with thumbnails.
    Groups files respecting Telegram's 10-item and 45MB limits.
    """
    current_group = []
    current_group_size = 0
    
    async def send_current_group():
        """Send accumulated media group and reset counters."""
        nonlocal current_group, current_group_size
        
        if not current_group:
            return
        
        try:
            await message.answer_media_group(media=current_group)
            print(f"[Uploader] ✅ Sent media group with {len(current_group)} items")
            await asyncio.sleep(2)  # Anti-flood delay
        except Exception as e:
            print(f"[Uploader] ❌ Media group failed: {e}")
            # Fallback: Send files individually
            for item in current_group:
                try:
                    if isinstance(item, InputMediaVideo):
                        await message.answer_video(item.media, thumbnail=item.thumbnail)
                    else:
                        await message.answer_photo(item.media)
                    await asyncio.sleep(1)
                except Exception as e2:
                    print(f"[Uploader] Fallback upload failed: {e2}")
        
        finally:
            current_group, current_group_size = [], 0
    
    for file_path in files:
        try:
            file_size = os.path.getsize(file_path)
            
            # Skip files that are too large
            if file_size > MAX_SINGLE_FILE:
                print(f"[Uploader] Skipping large file: {file_path} ({file_size / 1024 / 1024:.2f}MB)")
                continue
            
            # Check if we need to send current group before adding this file
            if (current_group_size + file_size > MAX_CHUNK_SIZE) or (len(current_group) >= MAX_GROUP_SIZE):
                await send_current_group()
            
            # Determine media type
            is_video = file_path.lower().endswith(('.mp4', '.mov', '.m4v'))
            is_photo = file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
            
            if not (is_video or is_photo):
                continue
            
            # Create media item
            file_input = FSInputFile(file_path)
            
            if is_video:
                thumbnail = _find_thumbnail(file_path)
                media_item = InputMediaVideo(media=file_input, thumbnail=thumbnail)
            else:
                media_item = InputMediaPhoto(media=file_input)
            
            # Add caption to first item only
            if not current_group and caption:
                media_item.caption = caption
            
            current_group.append(media_item)
            current_group_size += file_size
            
        except Exception as e:
            print(f"[Uploader] Error processing {file_path}: {e}")
    
    # Send remaining items
    await send_current_group()


def _find_thumbnail(video_path: str) -> FSInputFile:
    """
    Find thumbnail file for a video.
    
    Looks for image file with same base name as the video.
    Common pattern: video.mp4 -> video.jpg
    
    Args:
        video_path: Path to video file
        
    Returns:
        FSInputFile of thumbnail or None
    """
    base_name = os.path.splitext(video_path)[0]
    
    # Check for matching thumbnail with various extensions
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        thumb_path = base_name + ext
        if os.path.exists(thumb_path):
            try:
                return FSInputFile(thumb_path)
            except Exception as e:
                print(f"[Uploader] Failed to load thumbnail {thumb_path}: {e}")
    
    return None


def _is_thumbnail_file(file_path: str, all_files: list) -> bool:
    """
    Check if a file is a thumbnail for a video.
    
    A file is considered a thumbnail if:
    1. It's an image file (.jpg, .jpeg, .png, .webp)
    2. A video file with the same base name exists
    
    Args:
        file_path: Path to potential thumbnail
        all_files: List of all files in directory
        
    Returns:
        True if file is a thumbnail, False otherwise
    """
    if not file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        return False
    
    base_name = os.path.splitext(file_path)[0]
    
    # Check if corresponding video exists
    for ext in ['.mp4', '.mov', '.m4v']:
        video_path = base_name + ext
        if video_path in all_files or os.path.exists(video_path):
            return True
    
    return False