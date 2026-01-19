"""
Snapchat Video Downloader
Module for downloading videos from Snapchat using yt-dlp.
Uses web scraping to extract and download shared Snapchat media.
"""

from typing import Optional
import yt_dlp
import os

from Logic.utils.path import generate_target_dir

# ============================================================================
# Constants
# ============================================================================

# User-Agent to bypass Snapchat scraper detection
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# yt-dlp configuration options
YDL_OPTIONS = {
    "format": "best",
    "user_agent": USER_AGENT,
    "quiet": False,
    "no_warnings": False,
    "writethumbnail": True,
}

# ============================================================================
# Download Functions
# ============================================================================


def download_snapchat_video(url: str) -> Optional[str]:
    """
    Download a video from a Snapchat share URL.

    Extracts and downloads shared Snapchat media content to local storage.
    Uses yt-dlp with a realistic user-agent to bypass detection.

    Args:
        url: Snapchat share URL (typically from snapchat.com)

    Returns:
        Optional[str]: Path to downloaded video file, or None if download failed

    Example:
        >>> path = download_snapchat_video("https://snapchat.com/...")
        >>> if path:
        ...     print(f"Downloaded to: {path}")

    Raises:
        No exceptions raised - returns None on any error
    """
    try:
        # Create unique download directory
        target_dir = generate_target_dir("snapchat")
        os.makedirs(target_dir, exist_ok=True)

        print(f"[Snapchat] Downloading to: {target_dir}")

        # Configure yt-dlp with output template and options
        ydl_opts = {
            **YDL_OPTIONS,
            "outtmpl": os.path.join(
                target_dir, "media_%(autonumber)03d.%(ext)s"
            ),
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[Snapchat] Extracting video info from: {url}")
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            print(f"[Snapchat] ✅ Download successful: {file_path}")
            return file_path

    except yt_dlp.utils.DownloadError as e:
        print(f"[Snapchat] ❌ Download error: {e}")
        return None

    except Exception as e:
        print(f"[Snapchat] ❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return None