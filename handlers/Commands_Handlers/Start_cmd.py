from aiogram import types, Router,F
from aiogram.filters.command import CommandStart

from Logic.utils.user_tracker import save_user
from languages import get_text
from Logger import logger

router = Router()

@router.message(CommandStart()) 
async def start_cmd(message: types.Message):
    """
    Handle /start command.
    Sends welcome message with supported platforms.
    Logs user data to CSV.
    """
    # Detect user language (default to English)
    lang = message.from_user.language_code if message.from_user.language_code in ["ar", "en"] else "en"
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    language = message.from_user.language_code
    
    # Save user to CSV
    is_new = save_user(user_id, username, first_name, last_name, language)
    
    if is_new:
        logger.info(
            f"✅ New user registered: {user_id} "
            f"(@{username}) - Language: {lang}"
        )
    else:
        logger.info(
            f"User rejoined: {user_id} "
            f"(@{username})"
        )
    
    await message.answer(get_text("welcome", lang))
