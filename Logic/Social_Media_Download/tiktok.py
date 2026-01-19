"""
TikTok Content Downloader
Module for downloading TikTok videos and photo carousels.
Supports both individual videos and carousel uploads through dual-mode downloading.

Uses:
    - TikWM API: For detecting content type and downloading photo carousels
    - yt-dlp: For downloading video content with quality preservation
"""

from typing import Optional, Union, Dict, List
import os
import yt_dlp
import requests

from Token import Tiktok_cookies
from Logic.utils.path import generate_target_dir

# ============================================================================
# Constants
# ============================================================================

# TikWM API endpoint for metadata and carousel downloads
TIKWM_API_URL = "https://www.tikwm.com/api/"

# TikWM API request parameters
TIKWM_API_PARAMS = {
    "count": 12,
    "cursor": 0,
    "web": 1,
    "hd": 1,
}

# User-Agent for HTTP requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

# Valid video file extensions
VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".avi")

# Valid image file extensions (for carousels)
VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".heic")

# All valid media extensions
VALID_MEDIA_EXTENSIONS = VALID_VIDEO_EXTENSIONS + VALID_IMAGE_EXTENSIONS

# HTTP request timeout (seconds)
REQUEST_TIMEOUT = 30

# Maximum image chunk size for streaming download (bytes)
CHUNK_SIZE = 8192

# ============================================================================
# Helper Functions
# ============================================================================


def _log(message: str, verbose: bool = False):
    """
    Conditional logging helper.

    Args:
        message: Message to log
        verbose: Whether to output the message
    """
    if verbose:
        print(message)


def _download_carousel(
    post_data: Dict, target_dir: str, verbose: bool = False
) -> Optional[Dict]:
    """
    Download TikTok photo carousel (multiple images).

    Args:
        post_data: API response data containing image URLs
        target_dir: Directory to save images
        verbose: Enable verbose output

    Returns:
        Optional[Dict]: Carousel info or None if download failed
    """
    _log("[TikTok] Downloading carousel...", verbose)

    image_urls = post_data.get("images", [])
    downloaded_files: List[str] = []

    for idx, img_url in enumerate(image_urls, 1):
        try:
            img_response = requests.get(
                img_url, stream=True, timeout=REQUEST_TIMEOUT
            )
            if img_response.status_code == 200:
                filename = f"media_{idx:03d}.jpg"
                filepath = os.path.join(target_dir, filename)

                with open(filepath, "wb") as f:
                    for chunk in img_response.iter_content(
                        chunk_size=CHUNK_SIZE
                    ):
                        f.write(chunk)

                downloaded_files.append(filepath)
                _log(
                    f"  ✅ Downloaded image {idx}/{len(image_urls)}",
                    verbose,
                )
            else:
                _log(
                    f"  ⚠️  Image {idx} failed: HTTP {img_response.status_code}",
                    verbose,
                )

        except Exception as e:
            _log(
                f"  ⚠️  Failed to download image {idx}: {e}",
                verbose,
            )

    return {
        "type": "carousel",
        "author": post_data["author"]["unique_id"],
        "title": post_data.get("title", "post")[:50],
        "likes": post_data.get("digg_count", 0),
        "comments": post_data.get("comment_count", 0),
        "shares": post_data.get("share_count", 0),
        "file_count": len(downloaded_files),
        "files": downloaded_files,
        "path": target_dir,
    }


def _download_video(url: str, target_dir: str, verbose: bool = False) -> Optional[str]:
    """
    Download TikTok video using yt-dlp.

    Args:
        url: TikTok video URL
        target_dir: Directory to save video
        verbose: Enable verbose output

    Returns:
        Optional[str]: Path to video file or None if failed
    """
    _log("[TikTok] Downloading video...", verbose)

    ydl_opts = {
        "cookiefile": Tiktok_cookies,
        "outtmpl": os.path.join(
            target_dir, "media_%(autonumber)03d.%(ext)s"
        ),
        "quiet": not verbose,
        "no_warnings": not verbose,
        "format": "bestvideo+bestaudio/best",
        "writethumbnail": True,
        "noplaylist": False,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            _log("[TikTok] Downloading with yt-dlp...", verbose)
            ydl.download([url])

            # Find downloaded media files
            files = [
                f
                for f in os.listdir(target_dir)
                if f.lower().endswith(VALID_MEDIA_EXTENSIONS)
            ]

            if not files:
                _log("[TikTok] ❌ No video files downloaded", verbose)
                return None

            # Return directory for multiple files, single file path for one file
            if len(files) > 1:
                _log(
                    f"[TikTok] ✅ Downloaded {len(files)} files",
                    verbose,
                )
                return target_dir
            else:
                file_path = os.path.join(target_dir, files[0])
                _log(f"[TikTok] ✅ Downloaded: {file_path}", verbose)
                return file_path

    except Exception as e:
        _log(f"[TikTok] ❌ Video download error: {e}", verbose)
        return None


# ============================================================================
# Main Download Function
# ============================================================================


def download_tiktok(
    url: str, verbose: bool = False
) -> Optional[Union[str, Dict]]:
    """
    Download TikTok content (video or carousel).

    Main entry point for TikTok downloads. Detects content type and
    routes to appropriate downloader (carousel → images, video → yt-dlp).

    Args:
        url: TikTok post URL
        verbose: Enable verbose logging (default: False)

    Returns:
        Optional[Union[str, Dict]]: Path string for video, Dict for carousel, None on error

    Example:
        >>> # Download video
        >>> result = download_tiktok("https://www.tiktok.com/video/...")
        >>> if isinstance(result, str):
        ...     print(f"Video downloaded to: {result}")
        >>>
        >>> # Download carousel
        >>> result = download_tiktok("https://www.tiktok.com/video/...")
        >>> if isinstance(result, dict):
        ...     print(f"Downloaded {result['file_count']} images")
    """
    try:
        _log(f"[TikTok] Processing URL: {url}", verbose)

        # Create unique download directory
        target_dir = generate_target_dir("tiktok")
        os.makedirs(target_dir, exist_ok=True)
        _log(f"[TikTok] Target directory: {target_dir}", verbose)

        # Query TikWM API to get metadata and detect content type
        _log("[TikTok] Querying TikWM API...", verbose)

        response = requests.post(
            TIKWM_API_URL,
            data={**TIKWM_API_PARAMS, "url": url},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            _log(
                f"[TikTok] ❌ API request failed: "
                f"HTTP {response.status_code}",
                verbose,
            )
            return None

        data = response.json()

        if data.get("code") != 0:
            _log(
                f"[TikTok] ❌ API error: {data.get('msg', 'Unknown')}",
                verbose,
            )
            return None

        post_data = data["data"]

        # Detect content type and download accordingly
        if "images" in post_data and post_data["images"]:
            # Carousel (photo slide)
            _log("[TikTok] Content type: Photo carousel", verbose)
            result = _download_carousel(post_data, target_dir, verbose)
            if result and result["files"]:
                return result
            return None

        else:
            # Video
            _log("[TikTok] Content type: Video", verbose)
            return _download_video(url, target_dir, verbose)

    except requests.exceptions.Timeout:
        _log("[TikTok] ❌ API request timeout", verbose)
        return None

    except requests.exceptions.RequestException as e:
        _log(f"[TikTok] ❌ Network error: {e}", verbose)
        return None

    except Exception as e:
        _log(f"[TikTok] ❌ Unexpected error: {e}", verbose)
        import traceback

        traceback.print_exc()
        return None