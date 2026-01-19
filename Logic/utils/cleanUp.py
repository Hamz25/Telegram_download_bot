"""
File and Directory Cleanup Management
Provides utilities for automatic cleanup and disk space monitoring.
"""

import os
import shutil
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup(path: str, delay: int = 0) -> bool:
    """
    Asynchronously clean up files or directories.
    
    IMPORTANT: This function now properly handles cleanup by:
    1. Waiting for the specified delay
    2. Checking if path still exists (may be deleted by another process)
    3. Using aggressive removal methods to ensure cleanup succeeds
    
    Args:
        path: Path to file or directory to clean up
        delay: Seconds to wait before cleanup (default: 0)
        
    Returns:
        bool: True if cleanup successful, False otherwise
    """
    # Wait for delay
    if delay > 0:
        await asyncio.sleep(delay)
    
    # Validate path exists
    if not path or not os.path.exists(path):
        logger.debug(f"Cleanup skipped - path doesn't exist: {path}")
        return False
    
    try:
        if os.path.isdir(path):
            # Remove entire directory tree
            logger.info(f"🧹 Cleaning up directory: {path}")
            shutil.rmtree(path, ignore_errors=True)
            
            # Verify removal
            if os.path.exists(path):
                # Try again with onerror handler
                def handle_remove_error(func, path, exc_info):
                    """Handle permission errors during removal."""
                    try:
                        os.chmod(path, 0o777)
                        func(path)
                    except Exception:
                        pass
                
                shutil.rmtree(path, onerror=handle_remove_error)
            
            logger.info(f"✅ Cleaned up directory: {path}")
        else:
            # Remove single file
            logger.info(f"🧹 Cleaning up file: {path}")
            os.remove(path)
            logger.info(f"✅ Cleaned up file: {path}")
        
        return True
        
    except PermissionError as e:
        logger.error(f"❌ Permission denied during cleanup: {path}")
        # Final aggressive attempt
        try:
            await asyncio.sleep(2)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            logger.info(f"✅ Retry cleaned up: {path}")
            return True
        except Exception:
            logger.error(f"❌ Retry cleanup failed for {path}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Cleanup failed for {path}: {e}")
        # Final attempt with ignore_errors
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            logger.info(f"✅ Force cleaned up: {path}")
            return True
        except Exception:
            return False


async def cleanup_old_downloads(
    downloads_dir: str = "downloads", max_age_hours: int = 24
) -> int:
    """
    Clean up old files in the downloads directory.
    
    Removes files and directories older than the specified age.
    
    Args:
        downloads_dir: Path to downloads directory (default: "downloads")
        max_age_hours: Maximum age of files in hours (default: 24)
        
    Returns:
        int: Number of items cleaned up
    """
    if not os.path.exists(downloads_dir):
        logger.debug(f"Downloads directory doesn't exist: {downloads_dir}")
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    try:
        for item in os.listdir(downloads_dir):
            item_path = os.path.join(downloads_dir, item)
            
            try:
                # Check item age
                item_age = current_time - os.path.getmtime(item_path)
                
                # Only clean if file is old enough
                if item_age > max_age_seconds:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                        cleaned_count += 1
                        age_hours = item_age / 3600
                        logger.info(f"🧹 Removed old directory: {item_path} (age: {age_hours:.1f}h)")
                    else:
                        os.remove(item_path)
                        cleaned_count += 1
                        age_hours = item_age / 3600
                        logger.info(f"🧹 Removed old file: {item_path} (age: {age_hours:.1f}h)")
                        
            except FileNotFoundError:
                # File deleted by another process
                continue
            except Exception as e:
                logger.error(f"❌ Failed to clean up {item_path}: {e}")
                continue
        
        if cleaned_count > 0:
            logger.info(f"✅ Cleaned up {cleaned_count} old items from {downloads_dir}")
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"❌ Error during old downloads cleanup: {e}")
        return 0


def get_directory_size(path: str) -> int:
    """
    Calculate total size of a directory in bytes.
    
    Args:
        path: Path to directory
        
    Returns:
        int: Total size in bytes
    """
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"❌ Error calculating directory size: {e}")
    
    return total_size


async def check_disk_space(
    downloads_dir: str = "downloads", min_free_gb: float = 1.0
) -> bool:
    """
    Check if there's sufficient disk space available.
    
    Args:
        downloads_dir: Path to downloads directory
        min_free_gb: Minimum free space required in GB (default: 1.0)
        
    Returns:
        bool: True if sufficient space available, False otherwise
    """
    try:
        import shutil as sh
        
        total, used, free = sh.disk_usage(downloads_dir)
        free_gb = free / (1024 ** 3)
        
        if free_gb < min_free_gb:
            logger.warning(
                f"⚠️ Low disk space: {free_gb:.2f}GB free "
                f"(minimum: {min_free_gb}GB)"
            )
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking disk space: {e}")
        return True  # Assume OK if check fails

        
async def periodic_cleanup():
    """
    Background task to periodically clean up old downloads.
    Runs every 6 hours to remove files older than 24 hours.
    """
    while True:
        try:
            await asyncio.sleep(6 * 3600)  # Wait 6 hours
            
            logger.info("🧹 Running periodic cleanup...")
            cleaned_count = await cleanup_old_downloads(
                downloads_dir="downloads",
                max_age_hours=24
            )
            
            if cleaned_count > 0:
                logger.info(f"✅ Cleaned up {cleaned_count} old items")
            
            # Check disk space
            space_ok = await check_disk_space(
                downloads_dir="downloads",
                min_free_gb=1.0
            )
            
            if not space_ok:
                logger.warning("⚠️ Low disk space detected!")
                
        except Exception as e:
            logger.error(f"❌ Error in periodic cleanup: {e}")
