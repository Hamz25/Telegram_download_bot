import os
import glob
from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto
from languages import get_text
from Logic.cleanUp import cleanup 

async def safe_upload(message: types.Message, path: str, lang: str, media_type: str = "video", 
                      caption: str = None, title: str = None, 
                      performer: str = None, thumbnail_url: str = None):
    
    # DEBUG: See where the bot is looking
    print(f"DEBUG: Checking path: {path}")

    if not path or not os.path.exists(path):
        await message.answer(get_text("error_general", lang).format(e=f"File not found at {path}"))
        return

    # --- CASE 1: FOLDER (10 Pictures) ---
    if os.path.isdir(path):
        # Look for images and specifically exclude the .json/xz files instaloader creates
        files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            files.extend(glob.glob(os.path.join(path, ext)))
        
        files.sort() # Keep order

        if not files:
            await message.answer(get_text("no_media", lang))
            await cleanup(path)
            return

        media_group = []
        for i, file_path in enumerate(files[:10]):
            photo = FSInputFile(file_path)
            media_group.append(InputMediaPhoto(media=photo, caption=caption if i == 0 else None))
        
        try:
            await message.answer_media_group(media=media_group)
        except Exception as e:
            await message.answer(get_text("error_general", lang).format(e=e))
        finally:
            await cleanup(path)
            return

    # --- CASE 2: SINGLE FILE (Reels/TikTok) ---
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