import os
import glob
import asyncio
from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from languages import get_text
from Logic.cleanUp import cleanup 

# Telegram Bot API limit is 50MB (52,428,800 bytes)
MAX_CHUNK_SIZE = 45 * 1024 * 1024  # 45MB threshold
MAX_SINGLE_FILE = 50 * 1024 * 1024 # 50MB absolute limit

async def safe_upload(message: types.Message, path: str, lang: str, media_type: str = "video", 
                      caption: str = None, title: str = None, 
                      performer: str = None, thumbnail_url: str = None):
    
    if not path or not os.path.exists(path):
        await message.answer(get_text("error_general", lang).format(e="File not found"))
        return

    # Determine what to clean: if path is a file, we clean its parent folder
    # This ensures thumbnails and temp files are deleted too.
    folder_to_clean = path if os.path.isdir(path) else os.path.dirname(path)

    try:
        if os.path.isdir(path):
            valid_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.m4v']
            files = []
            for ext in valid_extensions:
                files.extend(glob.glob(os.path.join(path, ext)))
            files = sorted(list(set(files)))

            if not files:
                await message.answer(get_text("no_media", lang))
                return

            current_group = []
            current_group_size = 0

            async def send_current_group():
                nonlocal current_group, current_group_size
                if not current_group:
                    return
                try:
                    # Only add caption to the very first file sent
                    await message.answer_media_group(media=current_group)
                    await asyncio.sleep(3) # Wait for Telegram to process
                except Exception as e:
                    print(f"Group Send Error: {e}")
                current_group = []
                current_group_size = 0

            for file_path in files:
                file_size = os.path.getsize(file_path)
                
                # 1. Skip if file is over 50MB (Cannot be sent via Bot API)
                if file_size > MAX_SINGLE_FILE:
                    print(f"Skipping {file_path}: {file_size} bytes is too large.")
                    continue

                is_video = file_path.lower().endswith(('.mp4', '.mov', '.m4v'))
                file_input = FSInputFile(file_path)
                
                # 2. If single file > 40MB, send any existing group first, then send this file alone
                if file_size > MAX_CHUNK_SIZE:
                    await send_current_group()
                    try:
                        if is_video:
                            await message.answer_video(file_input)
                        else:
                            await message.answer_photo(file_input)
                        await asyncio.sleep(0.5) # pause for sending a chunck of files to avoid collision
                    except Exception as e:
                        print(f"Large File Send Error: {e}")
                    continue

                # 3. If adding this file exceeds 40MB or group has 10 items, send group first
                if (current_group_size + file_size > MAX_CHUNK_SIZE) or (len(current_group) >= 10):
                    await send_current_group()

                # Add to group
                media_item = InputMediaVideo(media=file_input) if is_video else InputMediaPhoto(media=file_input)
                # Apply caption only to the first item of the first group
                if not current_group and not any(current_group): 
                    media_item.caption = caption

                current_group.append(media_item)
                current_group_size += file_size

            # Final flush
            await send_current_group()

        else:
            # SINGLE FILE CASE (Non-directory)
            file_size = os.path.getsize(path)
            if file_size > MAX_SINGLE_FILE:
                await message.answer("File is too large for Telegram (>50MB).")
            else:
                input_file = FSInputFile(path)
                if media_type == "video":
                    await message.answer_video(input_file, caption=caption)
                elif media_type == "photo":
                    await message.answer_photo(input_file, caption=caption)
                else:
                    thumb = FSInputFile(thumbnail_url) if thumbnail_url else None
                    await message.answer_audio(audio=input_file, caption=caption, 
                                              title=title, performer=performer, thumbnail=thumb)

    except Exception as e:
        print(f"Uploader Error: {e}")
        await message.answer(get_text("error_general", lang).format(e=str(e)))
    finally:
        # ALWAYS clean the folder after the process finishes
        # Increased delay to 60s to ensure Telegram has finished reading from disk
        await cleanup(folder_to_clean, delay=40)