# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State

# --- CUSTOM MODULES ---
from Token import TToken
# Import your router objects from the handlers files
from handlers.ytHandle import router as youtube_router
from handlers.SpotifyHandle import router as spotify_router
from handlers.socialHandle import router as social_router

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable used by handlers
botname = "-@spoonDbot"

# Define States here so they can be imported by handlers
class BotStates(StatesGroup):
    choosing_quality = State()

async def main():
    # Initialize bot with global HTML parse mode
    bot = Bot(token=TToken, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Ensure download directory exists
    os.makedirs("downloads", exist_ok=True)

    # Attach feature-specific routers to the main dispatcher
    dp.include_router(youtube_router)
    dp.include_router(spotify_router)
    dp.include_router(social_router)

    logging.info("Bot is starting...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Polling error: {e}")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Connection lost, restarting in 5 seconds... Error: {e}")
            import time
            time.sleep(5)