import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import FSInputFile

from Logic.tiktok import download_tiktok
from Logic.snapchat import download_snapchat_video
from Logic.insta import download_insta_reel, download_insta_story, download_insta_post
from languages import get_text
from Logic.Uploader import safe_upload
from Logic.cleanUp import cleanup

router = Router()


"""---------------------------------------------------------------------------------------------------------TikTok"""
@router.message(F.text.contains("tiktok.com"))
async def handle_tiktok(message: types.Message):
    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
    
    try:
        # Extract URL from message
        url = message.text.strip()
        print(f"[HANDLER] Processing TikTok URL: {url}")

        result = await asyncio.to_thread(download_tiktok,url)
        path = None
        # Run the download in a thread to keep the bot responsive
        if isinstance(result,dict):
            path = result.get('path') #Extract the path string from the dict
        else:
            path = result # it's already a string path (for videos)
        
        print(f"[HANDLER] Download result: {path}")
        
        # Delete status message
        try:
            await status_msg.delete()
        except:
            pass
        
        # Check if download was successful
        if path and os.path.exists(path):
            print(f"[HANDLER] Path exists, uploading...")
            await safe_upload(message, path, lang, caption=get_text("tiktok_success", lang))
        else:
            print(f"[HANDLER] Download failed - path is None or doesn't exist")
            await message.answer(get_text("no_media", lang))
            
            # Cleanup empty directory if it exists
            if path and os.path.isdir(path):
                await cleanup(path)
                
    except Exception as e:
        print(f"[HANDLER] Error in handle_tiktok: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await status_msg.delete()
        except:
            pass
        await message.answer(get_text("error_general", lang).format(e=e))



"""---------------------------------------------------------------------------------------------------------Snapchat"""
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



"""---------------------------------------------------------------------------------------------------------Instagram"""
@router.message(F.text.contains("instagram.com") | F.text.regexp(r'^@?[\w\.]+$'))
async def handle_instagram(message: types.Message):
    if message.text.startswith("/"): return

    lang = message.from_user.language_code
    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    url = message.text
    path = None

    try:
        # Case 1: Stories
        if "/stories/" in url or (not url.startswith("http") and not "/highlights/" in url):
            username = url.split("/stories/")[1].split("/")[0] if "/stories/" in url else url.replace("@", "")
            path = await asyncio.to_thread(download_insta_story, username)
            
            if path:
                await status_msg.delete()
                caption = get_text("insta_stories", lang).format(username=username)
                await safe_upload(message, path, lang, caption=caption)
            else:
                await status_msg.delete()
                await message.answer(get_text("no_media", lang))

        # Case 2: Highlights
        elif "/highlights/" in url or url.lower().startswith("highlight"):
            # Extract username from URL or command
            if "/highlights/" in url:
                username = url.split("instagram.com/")[1].split("/")[0]
            else:
                # Format: "highlight @username" or just "@username"
                username = url.replace("highlight", "").replace("@", "").strip()
            
            path = await asyncio.to_thread(download_insta_highlight, username)
            
            if path:
                await status_msg.delete()
                caption = f"📌 Highlights from @{username}"
                await safe_upload(message, path, lang, caption=caption)
            else:
                await status_msg.delete()
                await message.answer(get_text("no_media", lang))

        # Case 3: Posts
        elif "/p/" in url:
            path = await asyncio.to_thread(download_insta_post, url)
            
            if path:
                await status_msg.delete()
                await safe_upload(message, path, lang)
            else:
                await status_msg.delete()
                await message.answer(get_text("no_media", lang))

        # Case 4: Reels
        else:
            path = await asyncio.to_thread(download_insta_reel, url)
            
            if path:
                await status_msg.delete()
                await safe_upload(message, path, lang)
            else:
                await status_msg.delete()
                await message.answer(get_text("no_media", lang))

    except Exception as e:
        if status_msg:
            try:
                await status_msg.delete()
            except:
                pass
        await message.answer(get_text("error_general", lang).format(e=e))
        import traceback
        traceback.print_exc()