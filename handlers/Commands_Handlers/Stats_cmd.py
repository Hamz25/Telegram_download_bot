from aiogram import types, Router,F

from Logger import logger
from languages import get_text

import os

router = Router()   

@router.message(lambda message: message.text and message.text.startswith("/stats"))
async def stats_cmd(message: types.Message):
    """
    Handle /stats command (admin only).
    Shows bot statistics and system info.
    """
    # Simple admin check - you should implement proper admin verification
    if message.from_user.id not in []:  # Add admin user IDs here
        return
    
    try:
        from Logic.utils.cleanUp import get_directory_size
        
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            dir_size = get_directory_size(downloads_dir)
            file_count = sum([len(files) for _, _, files in os.walk(downloads_dir)])
            
            stats_msg = (
                f"📊 <b>Bot Statistics</b>\n\n"
                f"📁 Downloads Directory:\n"
                f"  • Size: {dir_size / (1024**2):.2f} MB\n"
                f"  • Files: {file_count}\n"
            )
        else:
            stats_msg = "📊 <b>Bot Statistics</b>\n\nNo downloads directory found."
        
        await message.answer(stats_msg)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.answer(f"❌ Error: {e}")
