from languages import get_text
from aiogram.utils.keyboard import InlineKeyboardBuilder

from languages import get_text


async def yt_options_keyboard(lang, message):
        builder = InlineKeyboardBuilder()
        builder.button(
            text=get_text("btn_video", lang), 
            callback_data=f"short_video_{message.message_id}"
            )
        builder.button(
            text=get_text("btn_audio", lang), 
            callback_data=f"short_audio_{message.message_id}"
            )
        builder.button(
        text=get_text("btn_voice", lang), 
            callback_data=f"short_voice_{message.message_id}"
            )
        builder.adjust(3)

async def yt_quality_keyboard(lang, message):
    builder = InlineKeyboardBuilder()

    # Add quality options
    for quality in ["360", "720", "1080"]:
        builder.button(text=f"🎬 {quality}p", callback_data=f"q_{quality}")

    # Add audio option
    builder.button(text="🎵 MP3", callback_data="q_audio")

    builder.adjust(2)  # 2 buttons per row
    return builder