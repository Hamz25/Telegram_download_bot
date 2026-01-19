import os
import asyncio
from aiogram import Router, F, types
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from Logic.utils.helpers import _delete_message_safely, _handle_download_error

from Logic.Social_Media_Download.insta import (
    download_insta_reel,
    download_insta_story,
    download_insta_post,
    download_insta_highlight,
    search_instagram_profile,
    get_profile_highlights,
)

from languages import get_text
from Logic.utils.Uploader import safe_upload

router = Router()

class InstagramStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_highlight_choice = State()



@router.message(F.text.contains("instagram.com"))
async def handle_instagram_url(message: types.Message):
    """Handle Instagram direct URL downloads (stories, reels, posts)."""
    lang = message.from_user.language_code or "en"
    url = message.text.strip()

    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    try:
        if "/stories/" in url:
            # Story
            username = url.split("/stories/")[1].split("/")[0]
            print(f"[Instagram] Downloading stories for @{username}")
            path = await asyncio.to_thread(download_insta_story, username)

            await _delete_message_safely(status_msg)
            
            if path:
                caption = get_text("insta_stories", lang).format(username=username)
                await safe_upload(message, path, lang, caption=caption)
            else:
                await message.answer(get_text("no_media", lang))

        elif "/reel/" in url or "/reels/" in url:
            # Reel
            print(f"[Instagram] Downloading reel")
            path = await asyncio.to_thread(download_insta_reel, url)

            await _delete_message_safely(status_msg)
            
            if path:
                await safe_upload(message, path, lang, caption=get_text("insta_reel_success", lang))
            else:
                await message.answer(get_text("no_media", lang))

        elif "/p/" in url or "/tv/" in url:
            # Post
            print(f"[Instagram] Downloading post")
            path = await asyncio.to_thread(download_insta_post, url)

            await _delete_message_safely(status_msg)
            
            if path:
                await safe_upload(message, path, lang, caption=get_text("insta_post_success", lang))
            else:
                await message.answer(get_text("no_media", lang))

        else:
            await _delete_message_safely(status_msg)
            await message.answer(get_text("error_unsupported_url", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)


# ============================================================================
# Instagram Username Handler (Profile Menu)
# ============================================================================

@router.message(F.text.regexp(r"^@?[\w\.]+$"))
async def handle_instagram_username(message: types.Message, state: FSMContext):
    """Handle Instagram username input - show profile menu."""
    # Ignore commands
    if message.text.startswith("/"):
        return
    
    lang = message.from_user.language_code or "en"
    username = message.text.strip().replace("@", "")
    
    # Basic validation
    if not username.replace("_", "").replace(".", "").isalnum():
        return
    
    status_msg = await message.answer(get_text("fetching", lang))
    
    try:
        print(f"[Instagram] Searching profile: {username}")
        
        profile_data = await asyncio.to_thread(search_instagram_profile, username)
        
        await _delete_message_safely(status_msg)
        
        if not profile_data:
            await message.answer(get_text("profile_not_found", lang).format(username=username))
            return
        
        # Save profile data
        await state.update_data(instagram_username=profile_data["username"])
        
        # Build keyboard with options
        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("btn_profile_details", lang), callback_data=f"ig_details_{profile_data['username']}")
        builder.button(text=get_text("btn_highlights", lang), callback_data=f"ig_highlights_{profile_data['username']}")
        builder.button(text=get_text("btn_stories", lang), callback_data=f"ig_stories_{profile_data['username']}")
        builder.adjust(1)
        
        # Format profile info
        profile_info = get_text("profile_found", lang).format(
            username=profile_data["username"],
            full_name=profile_data["full_name"] or "N/A",
            followers=f"{profile_data['followers']:,}",
            following=f"{profile_data['following']:,}",
            posts=f"{profile_data['posts_count']:,}",
            verified="✓" if profile_data["is_verified"] else "",
            private="🔒" if profile_data["is_private"] else "🔓",
        )
        
        await message.answer(profile_info, reply_markup=builder.as_markup())
        await state.set_state(InstagramStates.waiting_for_action)
        
    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)


# ============================================================================
# Instagram Profile Details Callback
# ============================================================================

@router.callback_query(F.data.startswith("ig_details_"))
async def handle_profile_details(callback: types.CallbackQuery, state: FSMContext):
    """Display detailed profile information."""
    lang = callback.from_user.language_code or "en"
    username = callback.data.split("_", 2)[2]
    
    await callback.answer()
    
    # FIXED: Delete button message
    await _delete_message_safely(callback.message)
    
    try:
        profile_data = await asyncio.to_thread(search_instagram_profile, username)
        
        if not profile_data:
            await callback.message.answer(get_text("profile_not_found", lang).format(username=username))
            await state.clear()
            return
        
        # Format detailed info
        details = get_text("profile_details", lang).format(
            username=profile_data["username"],
            full_name=profile_data["full_name"] or "N/A",
            bio=profile_data["biography"][:200] if profile_data["biography"] else get_text("no_bio", lang),
            followers=f"{profile_data['followers']:,}",
            following=f"{profile_data['following']:,}",
            posts=f"{profile_data['posts_count']:,}",
            verified=get_text("yes", lang) if profile_data["is_verified"] else get_text("no", lang),
            private=get_text("yes", lang) if profile_data["is_private"] else get_text("no", lang),
        )
        
        # Send with profile picture if available
        if profile_data.get("profile_pic_url"):
            try:
                await callback.message.answer_photo(photo=profile_data["profile_pic_url"], caption=details)
            except Exception:
                await callback.message.answer(details)
        else:
            await callback.message.answer(details)
        
        await state.clear()
        
    except Exception as e:
        await _handle_download_error(callback, lang, e)
        await state.clear()


# ============================================================================
# Instagram Highlights Request Callback
# ============================================================================

@router.callback_query(F.data.startswith("ig_highlights_"))
async def handle_highlights_request(callback: types.CallbackQuery, state: FSMContext):
    """Handle highlight download request."""
    lang = callback.from_user.language_code or "en"
    username = callback.data.split("_", 2)[2]
    
    await callback.answer()
    
    # FIXED: Delete button message
    await _delete_message_safely(callback.message)
    
    status_msg = await callback.message.answer(get_text("fetching", lang))
    
    try:
        print(f"[Instagram] Fetching highlights for @{username}")
        
        highlights = await asyncio.to_thread(get_profile_highlights, username)
        
        await _delete_message_safely(status_msg)
        
        if highlights is None:
            await callback.message.answer(get_text("error_private_profile", lang))
            await state.clear()
            return
        
        if not highlights:
            await callback.message.answer(get_text("no_highlights", lang).format(username=username))
            await state.clear()
            return
        
        if len(highlights) == 1:
            # Single highlight - download directly
            await callback.message.answer(get_text("downloading_highlight", lang))
            await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)
            
            path = await asyncio.to_thread(download_insta_highlight, username, 0)
            
            if path:
                await safe_upload(
                    callback.message,
                    path,
                    lang,
                    caption=get_text("highlight_success", lang).format(title=highlights[0]["title"]),
                )
            else:
                await callback.message.answer(get_text("no_media", lang))
            
            await state.clear()
        else:
            # Multiple highlights - show selection
            await state.update_data(instagram_username=username, highlights_list=highlights)
            
            builder = InlineKeyboardBuilder()
            for hl in highlights:
                button_text = f"{hl['title']} ({hl['item_count']} items)"
                builder.button(text=button_text[:64], callback_data=f"dl_hl_{hl['index']}")
            
            builder.button(text=get_text("btn_download_all_highlights", lang), callback_data="dl_hl_all")
            builder.adjust(1)
            
            await callback.message.answer(
                get_text("select_highlight", lang).format(count=len(highlights)),
                reply_markup=builder.as_markup(),
            )
            
            await state.set_state(InstagramStates.waiting_for_highlight_choice)
        
    except Exception as e:
        await _handle_download_error(callback, lang, e, status_msg)
        await state.clear()


# ============================================================================
# Instagram Highlight Download Callback
# ============================================================================

@router.callback_query(F.data.startswith("dl_hl_"))
async def handle_highlight_download(callback: types.CallbackQuery, state: FSMContext):
    """Download selected highlight(s)."""
    lang = callback.from_user.language_code or "en"
    
    await callback.answer()
    
    # FIXED: Delete selection menu
    await _delete_message_safely(callback.message)
    
    try:
        data = await state.get_data()
        username = data.get("instagram_username")
        highlights_list = data.get("highlights_list", [])
        
        if not username:
            await callback.message.answer(get_text("error_session_expired", lang))
            await state.clear()
            return
        
        selection = callback.data.split("_", 2)[2]
        
        status_msg = await callback.message.answer(get_text("downloading_highlight", lang))
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)
        
        if selection == "all":
            # Download all highlights
            print(f"[Instagram] Downloading all highlights for @{username}")
            path = await asyncio.to_thread(download_insta_highlight, username, None)
            
            await _delete_message_safely(status_msg)
            
            if path:
                await safe_upload(
                    callback.message,
                    path,
                    lang,
                    caption=get_text("all_highlights_success", lang).format(count=len(highlights_list)),
                )
            else:
                await callback.message.answer(get_text("no_media", lang))
        else:
            # Download specific highlight
            highlight_idx = int(selection)
            highlight_info = next((hl for hl in highlights_list if hl["index"] == highlight_idx), None)
            
            print(f"[Instagram] Downloading highlight #{highlight_idx} for @{username}")
            path = await asyncio.to_thread(download_insta_highlight, username, highlight_idx)
            
            await _delete_message_safely(status_msg)
            
            if path:
                await safe_upload(
                    callback.message,
                    path,
                    lang,
                    caption=get_text("highlight_success", lang).format(
                        title=highlight_info["title"] if highlight_info else "Highlight"
                    ),
                )
            else:
                await callback.message.answer(get_text("no_media", lang))
        
        await state.clear()
        
    except Exception as e:
        await _handle_download_error(callback, lang, e)
        await state.clear()


# ============================================================================
# Instagram Stories Download Callback
# ============================================================================

@router.callback_query(F.data.startswith("ig_stories_"))
async def handle_stories_download(callback: types.CallbackQuery, state: FSMContext):
    """Download all active stories for a profile."""
    lang = callback.from_user.language_code or "en"
    username = callback.data.split("_", 2)[2]
    
    await callback.answer()
    
    # FIXED: Delete button message
    await _delete_message_safely(callback.message)
    
    status_msg = await callback.message.answer(get_text("downloading_stories", lang))
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_VIDEO)
    
    try:
        print(f"[Instagram] Downloading stories for @{username}")
        
        path = await asyncio.to_thread(download_insta_story, username)
        
        await _delete_message_safely(status_msg)
        
        if path:
            await safe_upload(
                callback.message,
                path,
                lang,
                caption=get_text("insta_stories", lang).format(username=username),
            )
        else:
            await callback.message.answer(get_text("upload_failed", lang).format(username=username))
        
        await state.clear()
        
    except Exception as e:
        await _handle_download_error(callback, lang, e, status_msg)
        await state.clear()