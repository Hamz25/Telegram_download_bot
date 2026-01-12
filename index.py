# Main file to run the code 
import asyncio 
import logging
import os
from aiogram import Bot, Dispatcher, types  
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart

# --- CUSTOM MODULES ---
from Token import TToken
from languages import get_text  
# Import your router objects
from handlers.ytHandle import router as youtube_router
from handlers.SpotifyHandle import router as spotify_router
from handlers.socialHandle import router as social_router

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


botname = "-@spoonDbot" #This is for the botname Message

# Initialize Dispatcher
dp = Dispatcher()

# Define States i can add more if i want 
class BotStates(StatesGroup):
    choosing_quality = State()

@dp.message(CommandStart()) # When the user press /start 
async def start_cmd(message: types.Message):
    # Detect language or default to 'en'
    lang = message.from_user.language_code if message.from_user.language_code in ["ar", "en"] else "en"
    
    await message.answer(get_text("welcome", lang)) 

async def main():
    bot = Bot(token=TToken, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) #This is the Bot object to make a bot 
    
    os.makedirs("downloads", exist_ok=True) #To Make a file so it can store the files that the users send and want to download

    dp.include_router(youtube_router) #call the youtube handler
    dp.include_router(spotify_router) #call the spotify handler
    dp.include_router(social_router) #call the insta/snap/Tiktok etc... handler

    logging.info("Bot is starting...") #This will show in the terminal so we can tell the bot is running 
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())