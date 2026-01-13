import os
import glob
import asyncio
from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from languages import get_text
from Logic.cleanUp import cleanup 

async def safe_upload(message: types.Message, path: str, lang: str, media_type: str = "video", 
                      caption: str = None, title: str = None, 
                      performer: str = None, thumbnail_url: str = None):
    
    print(f"DEBUG: Checking path: {path}")

    if not path or not os.path.exists(path):
        await message.answer(get_text("error_general", lang).format(e=f"File not found at {path}"))
        return

    # CASE 1: DIRECTORY (Multiple files)
    if os.path.isdir(path):
        files = []

        # Case-insensitive file extension matching
        valid_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.heic', 
                          '*.JPG', '*.JPEG', '*.PNG', '*.WEBP', '*.HEIC',
                          '*.mp4', '*.mov', '*.m4v', 
                          '*.MP4', '*.MOV', '*.M4V']
        
        for ext in valid_extensions:
            files.extend(glob.glob(os.path.join(path, ext)))
        
        # Remove duplicates and sort
        files = sorted(list(set(files)))
        
        print(f"DEBUG: Found {len(files)} files in directory")

        if not files:
            await message.answer(get_text("no_media", lang))
            await cleanup(path)
            return

        # Send in chunks of 10 (Telegram's media group limit)
        for i in range(0, len(files), 10):
            chunk = files[i:i + 10]
            media_group = []
            
            for j, file_path in enumerate(chunk):
                is_video = file_path.lower().endswith(('.mp4', '.mov', '.m4v'))
                file_input = FSInputFile(file_path)
                # Only add caption to the first file of the first chunk
                current_caption = caption if (i == 0 and j == 0) else None
                
                if is_video:
                    media_group.append(InputMediaVideo(media=file_input, caption=current_caption))
                else:
                    media_group.append(InputMediaPhoto(media=file_input, caption=current_caption))
            
            try:
                await message.answer_media_group(media=media_group)
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error sending chunk {i//10 + 1}: {e}")
                await message.answer(get_text("error_general", lang).format(e=str(e)))

        await cleanup(path)
        return

    # CASE 2: SINGLE FILE
    try:
        input_file = FSInputFile(path)
        
        if media_type == "video":
            await message.answer_video(input_file, caption=caption)
        elif media_type == "photo":
            await message.answer_photo(input_file, caption=caption)
        else:
            await message.answer_audio(audio=input_file, caption=caption, 
                                      title=title, performer=performer)
    except Exception as e:
        print(f"Error sending single file: {e}")
        await message.answer(get_text("error_general", lang).format(e=str(e)))
    finally:
        await cleanup(path)