"""
Pinterest Media Downloader
Module for downloading Pinterest pins, boards, and profile galleries.

Strategy (in order, each only runs if the previous one fails):
  1. gallery-dl, anonymous - Pinterest serves public pins/boards without
     authentication in the vast majority of cases.
  2. gallery-dl with a cookies.txt file, if configured - needed for private
     boards or content gated behind login.
  3. yt-dlp - fallback for video pins only, different extractor entirely.
"""

import os
import re
import shutil
import asyncio
import logging
from typing import Optional, Dict

import yt_dlp

from Logic.utils.path import generate_target_dir

logger = logging.getLogger(__name__)

# --- Configuration ---

# NOTE: PIN_COOKIES must be a Netscape/Mozilla format cookies.txt exported
# from a logged-in browser session. Only needed for private boards/pins.
PIN_COOKIES: Optional[str] = os.getenv("Pinterest_cookies")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

GALLERY_DL_BIN = shutil.which("gallery-dl") or "gallery-dl"

# Boards/profiles can run into the thousands of pins - cap to keep runtime
# and Telegram media-group uploads sane.
MAX_GALLERY_ITEMS = 30


def _has_cookies() -> bool:
    """True only if a cookie file path is actually set AND exists on disk."""
    return bool(PIN_COOKIES) and os.path.exists(PIN_COOKIES)


def classify_pinterest_url(url: str) -> str:
    """
    Classify a Pinterest URL into 'pin', 'board', or 'profile'.

    Examples:
        pin.it/AbCdEf                                -> pin
        pinterest.com/pin/1234567890123/              -> pin
        pinterest.com/username/                       -> profile
        pinterest.com/username/board-name/             -> board
        pinterest.com/username/board-name/section/     -> board
    """
    clean_url = url.split("?")[0].rstrip("/")

    if "pin.it/" in clean_url:
        return "pin"

    match = re.search(r"pinterest\.[a-z.]+(/.*)", clean_url, re.IGNORECASE)
    if not match:
        return "pin"

    segments = [seg for seg in match.group(1).split("/") if seg]

    if not segments:
        return "profile"
    if segments[0].lower() == "pin":
        return "pin"
    if len(segments) == 1:
        return "profile"
    return "board"


# --- gallery-dl tier ---

async def _run_gallery_dl(
    url: str,
    target_dir: str,
    use_cookies: bool,
    extra_opts: Optional[list] = None,
) -> Optional[str]:
    os.makedirs(target_dir, exist_ok=True)

    command = [GALLERY_DL_BIN, "-D", target_dir, "--no-mtime"]

    if use_cookies and _has_cookies():
        command += ["--cookies", PIN_COOKIES]

    if extra_opts:
        command += extra_opts

    command.append(url)

    logger.info(f"[Pinterest] gallery-dl ({'cookies' if use_cookies else 'anonymous'}): {' '.join(command)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180.0)
        except asyncio.TimeoutError:
            process.kill()
            logger.warning("[Pinterest] gallery-dl timed out after 180 seconds")
            return None

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.info(f"[Pinterest] gallery-dl failed (code {process.returncode}): {error_msg}")
            return None

        files = [f for f in os.listdir(target_dir) if not f.startswith(".")] if os.path.exists(target_dir) else []
        if files:
            logger.info(f"[Pinterest] gallery-dl downloaded {len(files)} file(s)")
            return target_dir
        return None

    except FileNotFoundError:
        logger.error("[Pinterest] gallery-dl binary not found - pip install gallery-dl")
        return None
    except Exception as e:
        logger.error(f"[Pinterest] gallery-dl exception: {e}")
        return None


# --- yt-dlp tier (video pins only, last resort) ---

def _ydl_download_sync(url: str, opts: Dict) -> None:
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


async def _try_yt_dlp(url: str, target_dir: str) -> Optional[str]:
    os.makedirs(target_dir, exist_ok=True)

    opts: Dict = {
        "outtmpl": os.path.join(target_dir, "media_%(autonumber)03d.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "user_agent": USER_AGENT,
        "noplaylist": True,
    }
    if _has_cookies():
        opts["cookiefile"] = PIN_COOKIES

    try:
        logger.info("[Pinterest] yt-dlp fallback tier...")
        await asyncio.to_thread(_ydl_download_sync, url, opts)
    except Exception as e:
        logger.info(f"[Pinterest] yt-dlp fallback failed: {e}")
        return None

    files = [f for f in os.listdir(target_dir) if not f.startswith(".")]
    if files:
        logger.info(f"[Pinterest] yt-dlp downloaded {len(files)} file(s)")
        return target_dir
    return None


# --- Shared fallback chain ---

async def _download_with_fallback_chain(
    target_dir: str,
    url: str,
    extra_opts: Optional[list] = None,
    allow_ytdlp: bool = True,
) -> Optional[str]:
    # Tier 1: anonymous gallery-dl - works for the vast majority of public content
    result = await _run_gallery_dl(url, target_dir, use_cookies=False, extra_opts=extra_opts)
    if result:
        return result

    # Tier 2: gallery-dl with cookies, if we have one - for private/gated content
    if _has_cookies():
        result = await _run_gallery_dl(url, target_dir, use_cookies=True, extra_opts=extra_opts)
        if result:
            return result

    # Tier 3: yt-dlp - only useful for single video pins, last resort
    if allow_ytdlp:
        return await _try_yt_dlp(url, target_dir)

    return None


# --- Core Functions ---

async def download_pinterest_pin(url: str) -> Optional[str]:
    """Download a single pin - covers both image and video pins."""
    target_dir = generate_target_dir("pinterest_pin")
    return await _download_with_fallback_chain(target_dir, url, allow_ytdlp=True)


async def download_pinterest_board(url: str) -> Optional[str]:
    """Download a board (or board section) as a gallery of images/videos."""
    target_dir = generate_target_dir("pinterest_board")
    extra_opts = ["--range", f"1-{MAX_GALLERY_ITEMS}"]
    return await _download_with_fallback_chain(target_dir, url, extra_opts=extra_opts, allow_ytdlp=False)


async def download_pinterest_profile(url: str) -> Optional[str]:
    """Download a user's public pins as a gallery."""
    target_dir = generate_target_dir("pinterest_profile")
    extra_opts = ["--range", f"1-{MAX_GALLERY_ITEMS}"]
    return await _download_with_fallback_chain(target_dir, url, extra_opts=extra_opts, allow_ytdlp=False)


async def download_pinterest_content(url: str) -> Optional[str]:
    """
    Single entry point - classifies the URL and routes it to the right
    download function.
    """
    content_type = classify_pinterest_url(url)

    if content_type == "pin":
        return await download_pinterest_pin(url)
    elif content_type == "board":
        return await download_pinterest_board(url)
    else:
        return await download_pinterest_profile(url)
