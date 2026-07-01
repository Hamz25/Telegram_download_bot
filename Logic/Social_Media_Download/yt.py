"""
YouTube Media Downloader
Module for downloading YouTube videos, shorts, and audio.
Supports quality selection, audio extraction, and metadata retrieval.

Cookie strategy: always attempt the download anonymously first. Cookies
(Youtube_cookies env var, pointing at a cookies.txt file) are only used as
a retry when yt-dlp reports an actual auth/bot-check error - not by default.
Most public videos never need cookies at all; using them unconditionally
just adds unnecessary risk of the cookie session itself getting flagged.

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

# Constants

YOUTUBE_COOKIES: Optional[str] = os.getenv("Youtube_cookies")

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

# Substrings yt-dlp/YouTube use when a request actually needs auth - only
# retry with cookies if one of these shows up, otherwise a cookie retry
# would just be masking a different bug.
AUTH_ERROR_MARKERS = (
    "sign in to confirm",
    "confirm you're not a bot",
    "private video",
    "login required",
    "this video is only available for registered users",
    "age-restricted",
    "members-only",
)


def _has_cookies() -> bool:
    return bool(YOUTUBE_COOKIES) and os.path.exists(YOUTUBE_COOKIES)


def _is_auth_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in AUTH_ERROR_MARKERS)


# Helper Functions

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


# Video Information Retrieval

def get_video_info(url: str) -> Tuple[Dict, bool, int, str, Optional[str], int]:
    """
    Retrieve video information without downloading.

    Tries anonymously first; only retries with cookies if the failure is
    specifically an auth/bot-check error and cookies are configured.

    Returns:
        Tuple containing:
        - info (Dict): Full yt-dlp info dictionary
        - is_short (bool): True if YouTube Short detected
        - size (int): Estimated file size in bytes
        - title (str): Video title
        - thumbnail (Optional[str]): Thumbnail URL
        - duration (int): Video duration in seconds
    """
    attempts = [dict(YDL_INFO_OPTS)]
    if _has_cookies():
        with_cookies = dict(YDL_INFO_OPTS)
        with_cookies["cookiefile"] = YOUTUBE_COOKIES
        attempts.append(with_cookies)

    last_exc = None
    for i, opts in enumerate(attempts):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                tag = "with cookies" if "cookiefile" in opts else "anonymous"
                print(f"[YouTube] Fetching info ({tag}) for: {url}")

                info = ydl.extract_info(url, download=False)

                title = info.get("title", "Unknown Title")
                thumbnail = info.get("thumbnail")
                duration = info.get("duration", 0)
                size = info.get("filesize") or info.get("filesize_approx") or 0
                is_short = "shorts" in url or duration < SHORTS_DURATION_THRESHOLD

                print(
                    f"[YouTube] ✅ Retrieved info: {title} "
                    f"({duration}s, {'Short' if is_short else 'Regular'})"
                )
                return info, is_short, size, title, thumbnail, duration

        except Exception as e:
            last_exc = e
            is_last_attempt = i == len(attempts) - 1
            if not is_last_attempt and _is_auth_error(e):
                print(f"[YouTube] Anonymous info fetch needs auth ({e}) — retrying with cookies")
                continue
            break

    print(f"[YouTube] ❌ Error fetching video info: {last_exc}")
    return None, False, 0, "Unknown Title", None, 0


# Video/Audio Download

def download_youtube(url: str, quality: str = "720", is_audio: bool = False) -> Optional[Dict]:
    """
    Download YouTube video or audio.

    Always attempts the download anonymously first. Only retries with
    cookies if yt-dlp reports a genuine auth/bot-check error AND cookies
    are configured via the Youtube_cookies env var.

    Args:
        url: YouTube video URL
        quality: Video quality (default: "720")
        is_audio: If True, extract audio only as MP3 (default: False)

    Returns:
        Optional[Dict]: same structure as before (see original docstring).
    """
    print(f"[YouTube] Starting download...")
    print(f"[YouTube] URL: {url}")
    print(f"[YouTube] Quality: {quality}p, Audio: {is_audio}")

    target_dir = generate_target_dir("youtube")
    os.makedirs(target_dir, exist_ok=True)

    def _build_opts(use_cookies: bool) -> Dict:
        opts = {
            "outtmpl": os.path.join(target_dir, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "writethumbnail": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        }
        if is_audio:
            opts.update({"format": "bestaudio/best", "postprocessors": AUDIO_POSTPROCESSORS})
        else:
            opts["format"] = _build_quality_format(quality)
        if use_cookies:
            opts["cookiefile"] = YOUTUBE_COOKIES
        return opts

    attempts = [False]
    if _has_cookies():
        attempts.append(True)

    last_exc = None
    for i, use_cookies in enumerate(attempts):
        try:
            ydl_opts = _build_opts(use_cookies)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                tag = "with cookies" if use_cookies else "anonymous"
                print(f"[YouTube] Downloading ({tag})...")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            print(f"[YouTube] ✅ Download complete: {filename}")

            if is_audio:
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
                return {"path": filename}

        except Exception as e:
            last_exc = e
            is_last_attempt = i == len(attempts) - 1
            if not is_last_attempt and _is_auth_error(e):
                print(f"[YouTube] Anonymous download needs auth ({e}) — retrying with cookies")
                continue
            break

    print(f"[YouTube] ❌ Download error: {last_exc}")
    import traceback
    traceback.print_exc()
    return None