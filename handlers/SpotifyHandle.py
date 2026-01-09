import asyncio
import logging
from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.spotify import download_spotify_track
from languages import get_text
from Logic.Uploader import safe_upload 

router = Router()

@router.message(F.text.contains("spotify.com"))
async def handle_spotify(message: types.Message):
    from main import botname
    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VOICE)

    try:
        result = await asyncio.to_thread(download_spotify_track, message.text)
        await status_msg.delete()
        
        if result and result.get('path'):
            await safe_upload(
                message, 
                path=result['path'], 
                lang=lang, 
                media_type="audio",
                caption=botname,
                title=result.get('title'),
                performer=result.get('performer')
            )
    except Exception as e:
        await status_msg.delete()
        logging.error(f"Spotify Error: {e}")