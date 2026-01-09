import os
from aiogram import types
from aiogram.types import FSInputFile
from languages import get_text
from Logic.cleanUp import cleanup  # Use absolute import to fix your error

async def safe_upload(message: types.Message, path: str, lang: str, media_type: str = "video", 
                      caption: str = None, title: str = None, 
                      performer: str = None, thumbnail_url: str = None):
    if not path or not os.path.exists(path):
        await message.answer(get_text("error_general", lang).format(e="File not found"))
        return

    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb >= 50:
        await message.answer(get_text("file_too_large", lang).format(size=round(file_size_mb, 1)))
        await cleanup(path, delay=0)
        return

    try:
        input_file = FSInputFile(path)
        if media_type == "video":
            await message.answer_video(input_file, caption=caption)
        else:
            thumb = FSInputFile(thumbnail_url) if thumbnail_url and os.path.exists(thumbnail_url) else None
            await message.answer_audio(
                audio=input_file, caption=caption, title=title, 
                performer=performer, thumbnail=thumb
            )
            if thumbnail_url: await cleanup(thumbnail_url, delay=1)
    except Exception as e:
        await message.answer(get_text("error_general", lang).format(e=e))
    finally:
        await cleanup(path)