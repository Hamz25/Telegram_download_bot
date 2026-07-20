"""
File Uploader Module
Handles uploading media files to Telegram with proper error handling and cleanup.
"""

import os
import glob
import json
import subprocess
import asyncio
from typing import Optional, Dict
from pathlib import Path
from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from languages import get_text
from Logic.utils.cleanUp import cleanup 

# Telegram Bot API limits
MAX_CHUNK_SIZE = 45 * 1024 * 1024  # 45MB per media group
MAX_SINGLE_FILE = 50 * 1024 * 1024 # 50MB per file
MAX_GROUP_SIZE = 10                 # Max 10 items per media group

# ffmpeg/ffprobe binaries - overridable per environment (e.g. SpoonLab uses
# the .exe binaries checked into the repo root, spoonserver would point
# these at a Linux install). Defaults to whatever's on PATH.
FFMPEG_BIN = os.getenv("FFMPEG_PATH", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_PATH", "ffprobe")

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
    
    # Find (or generate) thumbnail + metadata for videos, so Telegram can
    # render an instant poster frame instead of a black placeholder while
    # it processes the file itself.
    thumbnail = _find_thumbnail(file_path) if media_type == "video" else None
    metadata = _get_video_metadata(file_path) if media_type == "video" else {}
    
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
                thumbnail=thumbnail,
                width=metadata.get("width"),
                height=metadata.get("height"),
                duration=metadata.get("duration"),
                supports_streaming=True,
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
                        await message.answer_video(
                            item.media,
                            thumbnail=item.thumbnail,
                            width=item.width,
                            height=item.height,
                            duration=item.duration,
                            supports_streaming=True,
                        )
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
            
            # Add caption to first item only
            item_caption = caption if (not current_group and caption) else None
            
            if is_video:
                thumbnail = _find_thumbnail(file_path)
                metadata = _get_video_metadata(file_path)
                media_item = InputMediaVideo(
                    media=file_input,
                    thumbnail=thumbnail,
                    caption=item_caption,
                    width=metadata.get("width"),
                    height=metadata.get("height"),
                    duration=metadata.get("duration"),
                    supports_streaming=True,
                )
            else:
                media_item = InputMediaPhoto(media=file_input, caption=item_caption)
            
            current_group.append(media_item)
            current_group_size += file_size
            
        except Exception as e:
            print(f"[Uploader] Error processing {file_path}: {e}")
    
    # Send remaining items
    await send_current_group()


def _get_video_metadata(video_path: str) -> Dict:
    """
    Probe a video with ffprobe for width/height/duration.

    Telegram uses this metadata (together with the thumbnail) to render the
    message instantly. Without it, Telegram has to inspect/process the raw
    video file itself before it can show anything, which is what produces
    the black placeholder on larger files.

    Returns an empty dict if ffprobe is unavailable or the probe fails -
    callers already treat missing keys as "let Telegram figure it out",
    so this fails safe.
    """
    try:
        result = subprocess.run(
            [
                FFPROBE_BIN, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height:format=duration",
                "-of", "json",
                video_path,
            ],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout or "{}")
        streams = data.get("streams") or [{}]
        stream = streams[0]
        duration_raw = data.get("format", {}).get("duration")

        return {
            "width": stream.get("width"),
            "height": stream.get("height"),
            "duration": int(float(duration_raw)) if duration_raw else None,
        }
    except FileNotFoundError:
        print("[Uploader] ffprobe not found on PATH — skipping video metadata.")
        return {}
    except Exception as e:
        print(f"[Uploader] ffprobe metadata failed for {video_path}: {e}")
        return {}


def _generate_thumbnail(video_path: str) -> Optional[str]:
    """
    Extract a poster frame into a sidecar jpg next to the video, e.g.
    media_001.mp4 -> media_001.jpg.

    This matches the exact naming convention _find_thumbnail already looks
    for, and _is_thumbnail_file already filters that pattern out of
    carousel uploads - so generating it here is a drop-in fix with no
    other logic needing to change.

    Grabs the frame at 1s in (skips potential black opening frames some
    platforms leave), falling back to the very first frame for clips
    shorter than 1s.
    """
    base_name = os.path.splitext(video_path)[0]
    thumb_path = base_name + ".jpg"

    if os.path.exists(thumb_path):
        return thumb_path

    def _extract(seek_args: list) -> bool:
        try:
            subprocess.run(
                [FFMPEG_BIN, "-y", *seek_args, "-i", video_path,
                 "-frames:v", "1", "-q:v", "2", thumb_path],
                capture_output=True, timeout=15,
            )
        except Exception as e:
            print(f"[Uploader] ffmpeg thumbnail generation failed for {video_path}: {e}")
            return False
        return os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0

    try:
        if _extract(["-ss", "00:00:01"]):
            return thumb_path
        # Clip shorter than 1s - retry from the very start.
        if _extract([]):
            return thumb_path
    except FileNotFoundError:
        print("[Uploader] ffmpeg not found on PATH — cannot generate thumbnails.")

    return None


def _find_thumbnail(video_path: str) -> Optional[FSInputFile]:
    """
    Find thumbnail file for a video.
    
    Looks for an image file with the same base name as the video first
    (e.g. video.mp4 -> video.jpg). If none exists, generates one from the
    video itself via ffmpeg.
    
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

    generated = _generate_thumbnail(video_path)
    if generated:
        try:
            return FSInputFile(generated)
        except Exception as e:
            print(f"[Uploader] Failed to load generated thumbnail {generated}: {e}")
    
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