"""
Instagram Media Downloader
Module for downloading Instagram posts, reels, stories, and highlights.

Strategy (in order, each only runs if the previous one fails):
  1. gallery-dl, anonymous - uses Instagram's REST API path, works for most
     public posts/reels even though instaloader's graphql endpoint is 403'd.
  2. gallery-dl with a cookies.txt (Netscape format) file, if configured -
     needed for content Instagram gates behind a login wall, and for
     stories/highlights.
  3. yt-dlp - different extractor entirely, last resort.
"""

import os
import shutil
import asyncio
import logging
import instaloader
import yt_dlp
from typing import Optional, Dict, List

from Logic.utils.path import generate_target_dir

logger = logging.getLogger(__name__)

# --- Configuration ---

# NOTE: INSTA_COOKIES must be a Netscape/Mozilla format cookies.txt exported
# from a logged-in browser session (e.g. "Get cookies.txt LOCALLY" extension).
# An instaloader session file will NOT work here - gallery-dl and yt-dlp both
# expect the Netscape cookie jar format.
INSTA_COOKIES: Optional[str] = os.getenv("Insta_cookies")
INSTA_USERNAME: Optional[str] = os.getenv("Insta_username")
INSTA_PASSWORD = os.getenv("Insta_password")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MOBILE_USER_AGENT = (
    "Instagram 150.0.0.33.120 Android (24/7.0; 480dpi; 1080x1920; "
    "Samsung; SM-G930F; herolte; samsungexynos8890; en_US)"
)

GALLERY_DL_BIN = shutil.which("gallery-dl") or "gallery-dl"


def _has_session() -> bool:
    """True only if a cookie file path is actually set AND exists on disk."""
    return bool(INSTA_COOKIES) and os.path.exists(INSTA_COOKIES)


# Initialize Instaloader API (kept for profile/highlight metadata lookups only)
L = instaloader.Instaloader(max_connection_attempts=1)
L.context.user_agent = MOBILE_USER_AGENT


if INSTA_USERNAME and INSTA_PASSWORD:
    try:
        L.login(INSTA_USERNAME, INSTA_PASSWORD)
        logger.info("[Instagram] Successfully logged in with credentials.")
    except Exception as e:
        logger.error(f"[Instagram] Login failed: {e}")
elif _has_session():
    try:
        L.load_session_from_file(INSTA_USERNAME or "", filename=INSTA_COOKIES)
    except Exception as e:
        logger.warning(f"[Instagram] Failed to load session file: {e}")

# --- gallery-dl tier ---

async def _run_gallery_dl(
    url: str,
    target_dir: str,
    use_cookies: bool,
    extra_opts: Optional[list] = None,
) -> Optional[str]:
    os.makedirs(target_dir, exist_ok=True)

    command = [GALLERY_DL_BIN, "-D", target_dir, "--no-mtime"]

    if use_cookies and _has_session():
        command += ["--cookies", INSTA_COOKIES]

    if extra_opts:
        command += extra_opts

    command.append(url)

    logger.info(f"[Instagram] gallery-dl ({'cookies' if use_cookies else 'anonymous'}): {' '.join(command)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
        except asyncio.TimeoutError:
            process.kill()
            logger.warning("[Instagram] gallery-dl timed out after 120 seconds")
            return None

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.info(f"[Instagram] gallery-dl failed (code {process.returncode}): {error_msg}")
            return None

        files = [f for f in os.listdir(target_dir) if not f.startswith(".")] if os.path.exists(target_dir) else []
        if files:
            logger.info(f"[Instagram] gallery-dl downloaded {len(files)} file(s)")
            return target_dir
        return None

    except FileNotFoundError:
        logger.error("[Instagram] gallery-dl binary not found - pip install gallery-dl")
        return None
    except Exception as e:
        logger.error(f"[Instagram] gallery-dl exception: {e}")
        return None


# --- yt-dlp tier (last resort) ---

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
    if _has_session():
        opts["cookiefile"] = INSTA_COOKIES

    try:
        logger.info("[Instagram] yt-dlp fallback tier...")
        await asyncio.to_thread(_ydl_download_sync, url, opts)
    except Exception as e:
        logger.info(f"[Instagram] yt-dlp fallback failed: {e}")
        return None

    files = [f for f in os.listdir(target_dir) if not f.startswith(".")]
    if files:
        logger.info(f"[Instagram] yt-dlp downloaded {len(files)} file(s)")
        return target_dir
    return None


async def _download_with_fallback_chain(target_dir: str, url: str) -> Optional[str]:
    """Shared tiered logic used by both posts and reels."""
    # Tier 1: anonymous gallery-dl - works for most public content
    result = await _run_gallery_dl(url, target_dir, use_cookies=False)
    if result:
        return result

    # Tier 2: gallery-dl with cookies, if we have one - for gated content
    if _has_session():
        result = await _run_gallery_dl(url, target_dir, use_cookies=True)
        if result:
            return result

    # Tier 3: yt-dlp - different extractor, last resort
    return await _try_yt_dlp(url, target_dir)


# --- Core Functions ---

async def download_insta_post(url: str) -> Optional[str]:
    target_dir = generate_target_dir("insta_post")
    return await _download_with_fallback_chain(target_dir, url)


async def download_insta_reel(url: str) -> Optional[str]:
    target_dir = generate_target_dir("insta_reel")
    return await _download_with_fallback_chain(target_dir, url)


async def download_insta_story(username: str) -> Optional[str]:
    """Download stories for a username. Stories require a logged-in session by
    nature (they're not public), so this always needs cookies configured."""
    if not _has_session():
        logger.warning("[Instagram] Stories require a cookies.txt file - none configured")
        return None
    target_dir = generate_target_dir(f"story_{username}")
    url = f"https://www.instagram.com/stories/{username}/"
    return await _run_gallery_dl(url, target_dir, use_cookies=True)


async def download_insta_highlight(username: str, highlight_id: Optional[int] = None) -> Optional[str]:
    """
    Download highlights for a username.

    Args:
        username: Instagram username
        highlight_id: Specific highlight index (int), None for all highlights

    Returns:
        Path to downloaded content or None
    """
    if not _has_session():
        logger.warning("[Instagram] Highlights require a cookies.txt file - none configured")
        return None

    target_dir = generate_target_dir(f"highlight_{username}")

    if highlight_id is not None:
        url = f"https://www.instagram.com/stories/highlights/{highlight_id}/"
        return await _run_gallery_dl(url, target_dir, use_cookies=True)
    else:
        url = f"https://www.instagram.com/{username}/"
        return await _run_gallery_dl(
            url, target_dir, use_cookies=True, extra_opts=["-o", "include=highlights"]
        )


# --- Metadata Functions ---

async def search_instagram_profile(username: str) -> Optional[Dict]:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
            return {
                'username': profile.username,
                'full_name': profile.full_name,
                'biography': profile.biography,
                'followers': profile.followers,
                'following': profile.followees,
                'posts_count': profile.mediacount,
                'is_private': profile.is_private,
                'is_verified': profile.is_verified,
                'profile_pic_url': profile.profile_pic_url,
                'userid': profile.userid,
            }
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"[Instagram] Retry {attempt + 1}/{max_retries} for profile search")
                await asyncio.sleep(2)
                continue
            logger.error(f"[Instagram] Profile search failed: {e}")
            return None
    return None


async def get_profile_highlights(username: str) -> Optional[List[Dict]]:
    """
    Get list of highlights for a profile.

    Returns:
        List of highlight dicts, empty list if none found, None if profile is private/error
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)

            if profile.is_private:
                logger.info(f"[Instagram] Profile @{username} is private")
                return None

            highlights = []
            hls = await asyncio.to_thread(list, L.get_highlights(profile))

            for hl in hls:
                highlights.append({
                    'index': hl.unique_id,
                    'title': hl.title,
                    'item_count': hl.itemcount,
                })

            return highlights

        except instaloader.exceptions.LoginRequiredException:
            logger.info(f"[Instagram] Login required to view @{username} highlights")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"[Instagram] Retry {attempt + 1}/{max_retries} for highlights fetch")
                await asyncio.sleep(2)
                continue
            logger.error(f"[Instagram] Highlights fetch failed: {e}")
            return []
    return []