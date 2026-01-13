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
        print(message.answer(get_text("error_general", lang).format(e=f"File not found at {path}")))
        return

    if os.path.isdir(path):
        files = []

        valid_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.heic', '*.mp4', '*.mov', '*.m4v']
        for ext in valid_extensions:
            files.extend(glob.glob(os.path.join(path, ext), recursive=True))
        
        files.sort()

        if not files:
            await message.answer(get_text("no_media", lang))
            await cleanup(path)
            return

        # Loop through chunks of 10
        for i in range(0, len(files), 10):
            chunk = files[i:i + 10]
            media_group = []
            
            for j, file_path in enumerate(chunk):
                is_video = file_path.lower().endswith(('.mp4', '.mov', '.m4v'))
                file_input = FSInputFile(file_path)
                current_caption = caption if (i == 0 and j == 0) else None
                
                if is_video:
                    media_group.append(InputMediaVideo(media=file_input, caption=current_caption))
                else:
                    media_group.append(InputMediaPhoto(media=file_input, caption=current_caption))
            
            try:
                await message.answer_media_group(media=media_group)
                # Wait briefly so Telegram doesn't mix the order of the albums
                await asyncio.sleep(1.5) 
            except Exception as e:
                print(f"Error sending chunk: {e}")

        # --- FIX: Cleanup and Return moved OUTSIDE the loop ---
        await cleanup(path)
        return

    # --- CASE 2: SINGLE FILE ---
    try:
        input_file = FSInputFile(path)
        if media_type == "video":
            await message.answer_video(input_file, caption=caption)
        else:
            await message.answer_audio(audio=input_file, caption=caption, title=title, performer=performer)
    except Exception as e:
        await message.answer(get_text("error_general", lang).format(e=e))
    finally:
        await cleanup(path)