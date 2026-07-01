"""
Instagram Media Downloader
Module for downloading Instagram posts, reels, stories, and highlights.

Strategy (in order, each only runs if the previous one fails):
  1. instaloader, anonymous (no login) - works for most public posts/reels.
  2. instaloader with a session cookie file, if one is configured - needed
     for content Instagram gates behind a login wall.
  3. yt-dlp - different extractor entirely, sometimes succeeds where
     instaloader is rate-limited or blocked.
"""

import os
import asyncio
import logging
import instaloader
import yt_dlp
from typing import Optional, Dict, List

from Logic.utils.path import generate_target_dir

logger = logging.getLogger(__name__)

# --- Configuration ---

# NOTE: os.getenv returns None if the var isn't set. Every use of this must
# go through _has_session() below - never call os.path.exists() on it
# directly, since os.path.exists(None) raises TypeError (this was the bug
# causing every download to silently fail before it even started).
INSTA_COOKIES: Optional[str] = os.getenv("Insta_cookies")
INSTA_USERNAME: Optional[str] = os.getenv("Insta_username")  # required by instaloader's session loader
INSTA_PASSWORD = os.getenv("Insta_password")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MOBILE_USER_AGENT = (
    "Instagram 150.0.0.33.120 Android (24/7.0; 480dpi; 1080x1920; "
    "Samsung; SM-G930F; herolte; samsungexynos8890; en_US)"
)


def _has_session() -> bool:
    """True only if a cookie file path is actually set AND exists on disk."""
    return bool(INSTA_COOKIES) and os.path.exists(INSTA_COOKIES)


# Initialize Instaloader API
L = instaloader.Instaloader(max_connection_attempts=1)
L.context.user_agent = MOBILE_USER_AGENT


if INSTA_USERNAME and INSTA_PASSWORD:
    try:
        L.login(INSTA_USERNAME, INSTA_PASSWORD)
        logger.info("[Instagram] Successfully logged in with credentials.")
    except Exception as e:
        logger.error(f"[Instagram] Login failed: {e}")
elif _has_session():
    if not INSTA_USERNAME:
        logger.warning(
            "[Instagram] Insta_cookies is set but Insta_username is not - "
            "session load will likely fail. Set Insta_username to the IG "
            "account the session file belongs to."
        )
    try:
        L.load_session_from_file(INSTA_USERNAME or "", filename=INSTA_COOKIES)
    except Exception as e:
        logger.warning(f"[Instagram] Failed to load session file: {e}")

# --- instaloader tier ---

async def _run_instaloader(args: list, target_dir: str, use_session: bool) -> Optional[str]:
    session_args = []
    if use_session:
        if INSTA_USERNAME and INSTA_PASSWORD:
            session_args = ["--login", INSTA_USERNAME, "--password", INSTA_PASSWORD]
        elif _has_session():
            session_args = ["--sessionfile", INSTA_COOKIES]

    base_command = [
        "instaloader",
        "--dirname-pattern", target_dir,
        "--filename-pattern", "{shortcode}",
        "--no-metadata-json",
        "--no-compress-json",
        "--no-captions",
        "--no-profile-pic",
        "--quiet",
    ] + session_args

    command = base_command + args
    logger.info(f"[Instagram] instaloader ({'session' if use_session else 'anonymous'}): {' '.join(command)}")

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
            logger.warning("[Instagram] instaloader timed out after 120 seconds")
            return None

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.info(f"[Instagram] instaloader failed (code {process.returncode}): {error_msg}")
            return None

        if os.path.exists(target_dir):
            for file in os.listdir(target_dir):
                if "profile_pic" in file:
                    os.remove(os.path.join(target_dir, file))

            files = os.listdir(target_dir)
            if files:
                logger.info(f"[Instagram] instaloader downloaded {len(files)} file(s)")
                return target_dir

        return None

    except Exception as e:
        logger.error(f"[Instagram] instaloader exception: {e}")
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
    if INSTA_USERNAME and INSTA_PASSWORD:
        opts["username"] = INSTA_USERNAME
        opts["password"] = INSTA_PASSWORD
    elif _has_session():
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


async def _download_with_fallback_chain(shortcode_args: list, target_dir: str, url: str) -> Optional[str]:
    """Shared tiered logic used by both posts and reels."""
    # Tier 1: anonymous instaloader - works for most public content
    result = await _run_instaloader(shortcode_args, target_dir, use_session=False)
    if result:
        return result

    # Tier 2: instaloader with session/login, if we have one - for gated content
    if (INSTA_USERNAME and INSTA_PASSWORD) or _has_session():
        result = await _run_instaloader(shortcode_args, target_dir, use_session=True)
        if result:
            return result

    # Tier 3: yt-dlp - different extractor, last resort
    return await _try_yt_dlp(url, target_dir)


# --- Core Functions ---

async def download_insta_post(url: str) -> Optional[str]:
    target_dir = generate_target_dir("insta_post")
    try:
        shortcode = url.split("/p/")[1].split("/")[0]
    except (IndexError, ValueError):
        logger.error(f"[Instagram] Could not parse shortcode from post URL: {url}")
        return None

    return await _download_with_fallback_chain(["--", f"-{shortcode}"], target_dir, url)


async def download_insta_reel(url: str) -> Optional[str]:
    target_dir = generate_target_dir("insta_reel")
    try:
        segment = "/reel/" if "/reel/" in url else "/reels/"
        shortcode = url.split(segment)[1].split("/")[0]
    except (IndexError, ValueError):
        logger.error(f"[Instagram] Could not parse shortcode from reel URL: {url}")
        return None

    return await _download_with_fallback_chain(["--", f"-{shortcode}"], target_dir, url)


async def download_insta_story(username: str) -> Optional[str]:
    """Download stories for a username. Stories require a logged-in session by
    nature (they're not public), so this always needs authentication set."""
    if not ((INSTA_USERNAME and INSTA_PASSWORD) or _has_session()):
        logger.warning("[Instagram] Stories require authentication - neither credentials nor cookies configured")
        return None
    target_dir = generate_target_dir(f"story_{username}")
    return await _run_instaloader(["--", f":stories-{username}"], target_dir, use_session=True)


async def download_insta_highlight(username: str, highlight_id: Optional[int] = None) -> Optional[str]:
    """
    Download highlights for a username.

    Args:
        username: Instagram username
        highlight_id: Specific highlight index (int), None for all highlights

    Returns:
        Path to downloaded content or None
    """
    if not ((INSTA_USERNAME and INSTA_PASSWORD) or _has_session()):
        logger.warning("[Instagram] Highlights require authentication - neither credentials nor cookies configured")
        return None

    target_dir = generate_target_dir(f"highlight_{username}")

    if highlight_id is not None:
        return await _run_instaloader(["--", f":hl-{highlight_id}"], target_dir, use_session=True)
    else:
        return await _run_instaloader(["--highlights", "--", username], target_dir, use_session=True)


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