import os
import shutil
import asyncio
import logging

async def cleanup(path: str, delay: int = 3):
    if not path or not os.path.exists(path):
        return
    await asyncio.sleep(delay)
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.remove(path)
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")