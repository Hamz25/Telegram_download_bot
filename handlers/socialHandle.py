import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import FSInputFile

from Logic.tiktok import download_tiktok
from Logic.snapchat import download_snapchat_video
from Logic.insta import download_insta_reel, download_insta_story
from languages import get_text
from Logic.Uploader import safe_upload
from Logic.cleanUp import cleanup

router = Router()

@router.message(F.text.contains("tiktok.com"))
async def handle_tiktok(message: types.Message):
    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
    try:
        path = await asyncio.to_thread(download_tiktok, message.text)
        await status_msg.delete()
        await safe_upload(message, path, lang, caption=get_text("tiktok_success", lang))
    except Exception as e:
        await status_msg.delete()
        await message.answer(get_text("error_general", lang).format(e=e))

@router.message(F.text.contains("snapchat.com"))
async def handle_snap(message: types.Message):
    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
    try:
        path = await asyncio.to_thread(download_snapchat_video, message.text)
        await status_msg.delete()
        await safe_upload(message, path, lang, caption=get_text("snap_success", lang))
    except Exception as e:
        await status_msg.delete()
        await message.answer(get_text("error_general", lang).format(e=e))

@router.message(F.text.contains("instagram.com") | F.text.regexp(r'^@?[\w\.]+$'))
async def handle_instagram(message: types.Message):
    if message.text.startswith("/"): return
    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
    url = message.text
    try:
        if "/stories/" in url or not url.startswith("http"):
            username = url.split("/stories/")[1].split("/")[0] if "http" in url else url.replace("@", "")
            folder = await asyncio.to_thread(download_insta_story, username)
            await status_msg.delete()
            if folder and os.path.exists(folder):
                media = MediaGroupBuilder(caption=get_text("insta_stories", lang).format(username=username))
                files = [f for f in os.listdir(folder) if not f.endswith(('.json', '.txt'))]
                if not files:
                    await message.answer(get_text("no_media", lang))
                else:
                    for f in files[:10]:
                        path = os.path.join(folder, f)
                        if f.lower().endswith(('.mp4', '.m4v', '.mov')): media.add_video(FSInputFile(path))
                        else: media.add_photo(FSInputFile(path))
                    await message.answer_media_group(media.build())
                await cleanup(folder)
        else:
            path = await asyncio.to_thread(download_insta_reel, url)
            await status_msg.delete()
            await safe_upload(message, path, lang)
    except Exception as e:
        await status_msg.delete()
        await message.answer(get_text("error_general", lang).format(e=e))