from aiogram import Router, F, types
from aiogram.enums import ChatAction

from Logic.utils.helpers import _delete_message_safely, _handle_download_error

from Logic.Social_Media_Download.pinterest import (
    download_pinterest_pin,
    download_pinterest_board,
    download_pinterest_profile,
    classify_pinterest_url,
)

from languages import get_text
from Logic.utils.Uploader import safe_upload

router = Router()


@router.message(F.text.contains("pinterest.") | F.text.contains("pin.it/"))
async def handle_pinterest_url(message: types.Message):
    """Handle Pinterest pin, board, and profile downloads."""
    lang = message.from_user.language_code or "en"
    url = message.text.strip()

    content_type = classify_pinterest_url(url)

    status_msg = await message.answer(get_text("uploading", lang))
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    try:
        if content_type == "pin":
            print("[Pinterest] Downloading pin")
            path = await download_pinterest_pin(url)
            success_key = "pinterest_pin_success"

        elif content_type == "board":
            print("[Pinterest] Downloading board")
            path = await download_pinterest_board(url)
            success_key = "pinterest_board_success"

        else:
            print("[Pinterest] Downloading profile")
            path = await download_pinterest_profile(url)
            success_key = "pinterest_board_success"

        await _delete_message_safely(status_msg)

        if path:
            await safe_upload(message, path, lang, caption=get_text(success_key, lang))
        else:
            await message.answer(get_text("update", lang))

    except Exception as e:
        await _handle_download_error(message, lang, e, status_msg)