import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder

from Logic.yt import get_video_info, download_youtube
from languages import get_text
from Logic.Uploader import safe_upload

router = Router()

@router.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_youtube(message: types.Message, state: FSMContext):
    from index import BotStates  # Local import to avoid circular dependency
    lang = message.from_user.language_code
    try:
        info, is_short, _, title, _, _ = await asyncio.to_thread(get_video_info, message.text)
        if is_short:
            status = await message.answer(get_text("shorts_detected", lang))
            result = await asyncio.to_thread(download_youtube, message.text)
            await status.delete()
            await safe_upload(message, result['path'], lang, caption=f"✅ {title}")
        else:
            await state.update_data(yt_url=message.text)
            builder = InlineKeyboardBuilder()
            for q in ["360", "720", "1080"]:
                builder.button(text=f"🎬 {q}p", callback_data=f"q_{q}")
            builder.button(text="🎵 MP3", callback_data="q_audio")
            builder.adjust(2)
            await message.answer(f"📺 <b>{title}</b>\n{get_text('video_found', lang)}", reply_markup=builder.as_markup())
            await state.set_state(BotStates.choosing_quality)
    except Exception as e:
        await message.answer(get_text("error_general", lang).format(e=e))

@router.callback_query(F.data.startswith("q_"))
async def process_yt_quality(callback: types.CallbackQuery, state: FSMContext):
    from index import botname # Local import
    lang, choice = callback.from_user.language_code, callback.data.split("_")[1]
    data = await state.get_data()
    url = data.get("yt_url")
    
    status_msg = await callback.message.edit_text(get_text("uploading", lang))
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        is_audio = (choice == "audio")
        result = await asyncio.to_thread(download_youtube, url, quality=choice, is_audio=is_audio)
        await status_msg.delete()
        
        if is_audio:
            await safe_upload(callback.message, result["path"], lang, "audio", botname, result['title'], result['performer'], result['thumb'])
        else:
            await safe_upload(callback.message, result['path'], lang, caption=f"✅ {result.get('title', 'Video')}")
    except Exception as e:
        await callback.message.answer(get_text("error_general", lang).format(e=e))
    await state.clear()