from aiogram import types,Router,F
from languages import get_text

router = Router()

@router.message(lambda message: message.text and message.text.startswith("/help"))
async def help_cmd(message: types.Message):
    """
    Handle /help command.
    Provides usage instructions.
    """
    lang = message.from_user.language_code if message.from_user.language_code in ["ar", "en"] else "en"
    await message.answer(get_text("welcome", lang))
