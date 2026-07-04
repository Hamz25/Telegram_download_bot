"""
Main entry point for the Social Media Downloader Bot.
Handles bot initialization, routing, and command processing.
"""

import asyncio 
import os
from dotenv import load_dotenv
from Logic.Logger import logger

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
# Custom modules

load_dotenv()  # Load environment variables from .env file

from handlers.Social_Media_Handlers.ytHandle import router as youtube_router
from handlers.Social_Media_Handlers.SpotifyHandle import router as spotify_router
from handlers.Social_Media_Handlers.instagramHandle import router as insta_router
from handlers.Social_Media_Handlers.pinterestHandle import router as pinterest_router
from handlers.Social_Media_Handlers.TiktokHandle import router as tiktok_router
from handlers.Social_Media_Handlers.snapchatHandle import router as snapchat_router

from handlers.Commands_Handlers.Help_cmd import router as help_router
from handlers.Commands_Handlers.Report_cmd import router as report_router
from handlers.Commands_Handlers.Stats_cmd import router as stats_router
from handlers.Commands_Handlers.Start_cmd import router as start_router
from handlers.Commands_Handlers.test import router as test_router

from handlers.adminHandle import router as admin_router

from Logic.utils.cleanUp import cleanup_old_downloads, check_disk_space, periodic_cleanup

# Bot metadata
botname = "-@spoonDbot"

async def on_shutdown(bot: Bot):
    """
    Actions to perform when bot shuts down.
    """
    logger.info("🛑 Bot is shutting down...")
    
    # Optional: Final cleanup
    try:
        await cleanup_old_downloads(downloads_dir="downloads", max_age_hours=0)
        logger.info("✅ Final cleanup completed")
    except Exception as e:
        logger.error(f"❌ Shutdown cleanup error: {e}")
    
    logger.info("👋 Bot stopped")
    
async def on_startup(bot: Bot):
    """
    Actions to perform when bot starts.
    """
    logger.info("🤖 Bot is starting...")
    
    # Create downloads directory
    os.makedirs("downloads", exist_ok=True)
    logger.info("✅ Downloads directory ready")
    
    # Run initial cleanup
    try:
        cleaned = await cleanup_old_downloads(downloads_dir="downloads", max_age_hours=24)
        if cleaned > 0:
            logger.info(f"🧹 Cleaned up {cleaned} old files on startup")
    except Exception as e:
        logger.error(f"❌ Startup cleanup error: {e}")
    
    # Start periodic cleanup task
    asyncio.create_task(periodic_cleanup())
    logger.info("✅ Periodic cleanup task started")
    
    logger.info("🚀 Bot is ready!")


async def main():
    """
    Main function to start the bot.
    Initializes bot, registers routers, and starts polling.
    """
    try:
        # Fresh dispatcher every run - routers can only be attached once,
        # so this must not be a module-level singleton reused across restarts.
        dp = Dispatcher()

        # Initialize bot with HTML parse mode
        bot = Bot(
            token=os.getenv("TESTBOTT"),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Test bot token
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot authenticated: @{bot_info.username}")
        
        # Register routers in order of priority
        dp.include_router(start_router)
        dp.include_router(admin_router)
        dp.include_router(youtube_router)
        dp.include_router(spotify_router)
        dp.include_router(insta_router)
        dp.include_router(pinterest_router)
        dp.include_router(tiktok_router)
        dp.include_router(snapchat_router)
        dp.include_router(test_router)
        dp.include_router(help_router)
        dp.include_router(report_router)
        dp.include_router(stats_router)


        logger.info("✅ All routers registered\n")
        
        # Register startup/shutdown handlers
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        logger.info("✅ Startup and shutdown handlers registered\n")

        # Start polling
        logger.info("🔄 Starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    running = True
    while running:
        try:
            asyncio.run(main())
            # dp.start_polling() returns normally on a clean shutdown
            # (e.g. aiogram catches SIGINT internally) - treat that as done,
            # not as a reason to loop back into main() again.
            running = False

        except KeyboardInterrupt:
            logger.info("⚠️ Bot stopped by user (Ctrl+C)")
            running = False

        except Exception as e:
            logger.error(f"❌ Application error: {e}")
            running = False