# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types  # Corrected import
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart

# --- CUSTOM MODULES ---
from Token import TToken
from languages import get_text  # Added missing import
# Import your router objects
from handlers.ytHandle import router as youtube_router
from handlers.SpotifyHandle import router as spotify_router
from handlers.socialHandle import router as social_router

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable used by handlers
botname = "-@spoonDbot"

# Initialize Dispatcher
dp = Dispatcher()

# Define States
class BotStates(StatesGroup):
    choosing_quality = State()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    # Detect language or default to 'en'
    lang = message.from_user.language_code if message.from_user.language_code in ["ar", "en"] else "en"
    # get_text works now because it is imported
    await message.answer(get_text("welcome", lang))

async def main():
    bot = Bot(token=TToken, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    os.makedirs("downloads", exist_ok=True)

    dp.include_router(youtube_router)
    dp.include_router(spotify_router)
    dp.include_router(social_router)

    logging.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())