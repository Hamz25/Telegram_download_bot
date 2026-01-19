"""
YouTube Media Downloader
Module for downloading YouTube videos, shorts, and audio.
Supports quality selection, audio extraction, and metadata retrieval.

Capabilities:
    - Video download with quality selection (360p, 720p, 1080p)
    - YouTube Shorts detection and download
    - Audio-only download to MP3 with metadata
    - Thumbnail extraction and conversion
"""

from typing import Optional, Tuple, Dict
import yt_dlp
import os

from Logic.utils.path import generate_target_dir

# ============================================================================
# Constants
# ============================================================================

# yt-dlp options for metadata retrieval
YDL_INFO_OPTS = {
    "noplaylist": True,
    "quiet": True,
}

# Video quality thresholds for YouTube Shorts detection (seconds)
SHORTS_DURATION_THRESHOLD = 60

# Audio extraction settings
AUDIO_CODEC = "mp3"
AUDIO_BITRATE = "192"

# FFmpeg postprocessor configuration
AUDIO_POSTPROCESSORS = [
    {
        "key": "FFmpegExtractAudio",
        "preferredcodec": AUDIO_CODEC,
        "preferredquality": AUDIO_BITRATE,
    },
    {
        "key": "FFmpegThumbnailsConvertor",
        "format": "jpg",
        "when": "before_dl",
    },
]

# ============================================================================
# Helper Functions
# ============================================================================


def _build_quality_format(quality: str) -> str:
    """
    Build yt-dlp format string for specified quality.

    Args:
        quality: Quality string (e.g., '720', '1080')

    Returns:
        str: yt-dlp format selection string
    """
    return (
        f"bestvideo[height<={quality}][ext=mp4]+"
        f"bestaudio[ext=m4a]/best[ext=mp4]/best"
    )


def _get_audio_path(filename: str) -> str:
    """
    Get expected MP3 audio file path from base filename.

    Args:
        filename: Original downloaded filename

    Returns:
        str: Path with .mp3 extension
    """
    return filename.rsplit(".", 1)[0] + f".{AUDIO_CODEC}"


def _get_thumbnail_path(filename: str) -> Optional[str]:
    """
    Get expected thumbnail file path if it exists.

    Args:
        filename: Original downloaded filename

    Returns:
        Optional[str]: Thumbnail path if exists, None otherwise
    """
    thumb_path = filename.rsplit(".", 1)[0] + ".jpg"
    if os.path.exists(thumb_path):
        return thumb_path
    return None


# ============================================================================
# Video Information Retrieval
# ============================================================================


def get_video_info(url: str) -> Tuple[Dict, bool, int, str, Optional[str], int]:
    """
    Retrieve video information without downloading.

    Fetches metadata about a YouTube video including title, duration,
    thumbnail, file size, and detects if it's a YouTube Short.

    Args:
        url: YouTube video URL

    Returns:
        Tuple containing:
        - info (Dict): Full yt-dlp info dictionary
        - is_short (bool): True if YouTube Short detected
        - size (int): Estimated file size in bytes
        - title (str): Video title
        - thumbnail (Optional[str]): Thumbnail URL
        - duration (int): Video duration in seconds

    Example:
        >>> info, is_short, size, title, thumb, duration = get_video_info(url)
        >>> if is_short:
        ...     print("This is a YouTube Short")
        >>> else:
        ...     print(f"Duration: {duration}s, Size: ~{size / 1024 / 1024:.1f}MB")
    """
    try:
        with yt_dlp.YoutubeDL(YDL_INFO_OPTS) as ydl:
            print(f"[YouTube] Fetching info for: {url}")

            info = ydl.extract_info(url, download=False)

            title = info.get("title", "Unknown Title")
            thumbnail = info.get("thumbnail")
            duration = info.get("duration", 0)

            # Get file size (prefer exact over approximate)
            size = (
                info.get("filesize")
                or info.get("filesize_approx")
                or 0
            )

            # Detect YouTube Shorts by URL or duration
            is_short = "shorts" in url or duration < SHORTS_DURATION_THRESHOLD

            print(
                f"[YouTube] ✅ Retrieved info: {title} "
                f"({duration}s, {'Short' if is_short else 'Regular'})"
            )

            return info, is_short, size, title, thumbnail, duration

    except Exception as e:
        print(f"[YouTube] ❌ Error fetching video info: {e}")
        import traceback

        traceback.print_exc()
        return None, False, 0, "Unknown Title", None, 0


# ============================================================================
# Video/Audio Download
# ============================================================================


def download_youtube(url: str, quality: str = "720", is_audio: bool = False) -> Optional[Dict]:
    """
    Download YouTube video or audio.

    Downloads YouTube media at specified quality. For audio, extracts
    to MP3 with metadata (title, artist). For video, preserves quality
    up to specified resolution.

    Args:
        url: YouTube video URL
        quality: Video quality (default: "720")
                Valid values: "360", "720", "1080"
        is_audio: If True, extract audio only as MP3 (default: False)

    Returns:
        Optional[Dict]: Download result with structure:

        For video:
        ```python
        {
            "path": str,  # Path to downloaded video file
        }
        ```

        For audio:
        ```python
        {
            "path": str,           # Path to MP3 file
            "title": str,          # Track title
            "performer": str,      # Channel/uploader name
            "thumb": Optional[str], # Path to thumbnail JPG if available
            "folder": str,         # Directory containing files
        }
        ```

    Example:
        >>> # Download video in 720p
        >>> result = download_youtube(url, quality="720", is_audio=False)
        >>> if result:
        ...     print(f"Video: {result['path']}")
        >>>
        >>> # Download as MP3
        >>> result = download_youtube(url, quality="720", is_audio=True)
        >>> if result:
        ...     print(f"Audio: {result['path']}")
        ...     print(f"Artist: {result['performer']}")
    """
    try:
        print(f"[YouTube] Starting download...")
        print(f"[YouTube] URL: {url}")
        print(f"[YouTube] Quality: {quality}p, Audio: {is_audio}")

        # Create target directory
        target_dir = generate_target_dir("youtube")
        os.makedirs(target_dir, exist_ok=True)

        # Build base yt-dlp options
        ydl_opts = {
            "outtmpl": os.path.join(target_dir, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "writethumbnail": True,
        }

        if is_audio:
            # Audio-only download configuration
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": AUDIO_POSTPROCESSORS,
            })
        else:
            # Video download configuration
            ydl_opts["format"] = _build_quality_format(quality)

        # Download media
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("[YouTube] Downloading...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            print(f"[YouTube] ✅ Download complete: {filename}")

            if is_audio:
                # Audio extraction result
                audio_path = _get_audio_path(filename)
                thumb_path = _get_thumbnail_path(filename)

                return {
                    "path": audio_path,
                    "title": info.get("title", "Unknown Title"),
                    "performer": info.get("uploader", "Unknown Artist"),
                    "thumb": thumb_path,
                    "folder": target_dir,
                }
            else:
                # Video result
                return {"path": filename}

    except Exception as e:
        print(f"[YouTube] ❌ Download error: {e}")
        import traceback

        traceback.print_exc()
        return None