"""
Facebook Downloader
Downloads Facebook videos (posts, reels, watch links) and photo posts at
the highest available quality.

Facebook video is well supported by yt-dlp, so that goes first here (the
reverse order of x.py/threads.py, where gallery-dl leads). gallery-dl is
kept as a fallback for photo-only posts, which yt-dlp can't extract.

Strategy (in order, each one only runs if the previous one fails):
  1. yt-dlp Python API, anonymous - primary path for videos/reels.
  2. yt-dlp Python API, with cookies - only if a cookie file is configured AND
     tier 1 actually failed (many FB videos require a logged-in session).
  3. yt-dlp CLI with --impersonate chrome, anonymous.
  4. yt-dlp CLI with --impersonate chrome, with cookies.
  5. gallery-dl, anonymous - fallback for photo posts.
  6. gallery-dl, with cookies - final fallback.
"""

from typing import Optional, Union, Dict, List
from urllib.parse import urlparse, urlunparse
import os
import subprocess
import yt_dlp
import requests

from Logic.utils.path import generate_target_dir

FACEBOOK_COOKIES: Optional[str] = os.getenv("Facebook_cookies")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".avi")
VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".heic")
VALID_MEDIA_EXTENSIONS = VALID_VIDEO_EXTENSIONS + VALID_IMAGE_EXTENSIONS

REQUEST_TIMEOUT = 30
GALLERY_DL_TIMEOUT = 60


def _has_cookies() -> bool:
    return bool(FACEBOOK_COOKIES) and os.path.isfile(FACEBOOK_COOKIES)


def _log(message: str, verbose: bool = False) -> None:
    if verbose:
        print(message)


def _clean_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _resolve_url(url: str, verbose: bool = False) -> str:
    """Resolve fb.watch short links to their canonical form and strip tracking params."""
    short_domains = ("fb.watch",)

    if any(d in url for d in short_domains):
        try:
            response = requests.head(
                url,
                allow_redirects=True,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            url = response.url
            _log(f"[Facebook] Resolved short URL to: {url}", verbose)
        except Exception as exc:
            _log(f"[Facebook] Could not resolve short URL ({exc}) — using original.", verbose)

    return _clean_url(url)


def _build_ydl_opts(target_dir: str, verbose: bool, use_cookies: bool = False) -> Dict:
    opts: Dict = {
        "outtmpl": os.path.join(target_dir, "media_%(autonumber)03d.%(ext)s"),
        "quiet": not verbose,
        "no_warnings": not verbose,
        "format": "bestvideo*+bestaudio/best",
        "format_sort": ["res", "fps", "tbr", "vcodec:h264"],
        "merge_output_format": "mp4",
        "noplaylist": False,
        "force_ipv4": True,
        "socket_timeout": 15,
    }

    if use_cookies and _has_cookies():
        opts["cookiefile"] = FACEBOOK_COOKIES

    return opts


def _collect_media_files(target_dir: str) -> List[str]:
    return [f for f in os.listdir(target_dir) if f.lower().endswith(VALID_MEDIA_EXTENSIONS)]


def _download_video_cli(url: str, target_dir: str, verbose: bool = False, use_cookies: bool = False) -> Optional[str]:
    outtmpl = os.path.join(target_dir, "media_%(autonumber)03d.%(ext)s")

    cmd = [
        "yt-dlp",
        "--impersonate", "chrome",
        "--format", "bestvideo*+bestaudio/best",
        "--format-sort", "res,fps,tbr",
        "--merge-output-format", "mp4",
        "--output", outtmpl,
        "--no-playlist",
    ]
    if use_cookies and _has_cookies():
        cmd += ["--cookies", FACEBOOK_COOKIES]
    cmd.append(url)

    _log(f"[Facebook] Running CLI ({'with cookies' if use_cookies else 'anonymous'}): {' '.join(cmd)}", verbose)

    try:
        subprocess.run(cmd, capture_output=not verbose, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        _log("[Facebook] yt-dlp CLI timed out after 120s", verbose)
    except FileNotFoundError:
        _log("[Facebook] yt-dlp CLI not found — is it installed?", verbose)
        return None
    except Exception as exc:
        _log(f"[Facebook] yt-dlp CLI error: {exc}", verbose)

    files = _collect_media_files(target_dir)
    if not files:
        return None
    if len(files) > 1:
        _log(f"[Facebook] ✅ CLI downloaded {len(files)} files → {target_dir}", verbose)
        return target_dir

    file_path = os.path.join(target_dir, files[0])
    _log(f"[Facebook] ✅ CLI downloaded: {file_path}", verbose)
    return file_path


def _download_gallery_dl(url: str, target_dir: str, verbose: bool = False, use_cookies: bool = False) -> List[str]:
    cmd = [
        "gallery-dl",
        "--dest", target_dir,
        "-o", "filename={num:>03}_{filename}.{extension}",
        "--no-mtime",
    ]
    if use_cookies and _has_cookies():
        cmd += ["--cookies", FACEBOOK_COOKIES]
    cmd.append(url)

    _log(f"[Facebook] Running gallery-dl ({'with cookies' if use_cookies else 'anonymous'}): {' '.join(cmd)}", verbose)

    try:
        subprocess.run(cmd, capture_output=not verbose, text=True, timeout=GALLERY_DL_TIMEOUT)
    except subprocess.TimeoutExpired:
        _log("[Facebook] gallery-dl timed out", verbose)
    except FileNotFoundError:
        _log("[Facebook] gallery-dl not found — is it installed?", verbose)
        return []
    except Exception as exc:
        _log(f"[Facebook] gallery-dl error: {exc}", verbose)

    return _collect_media_files(target_dir)


def _finalize(target_dir: str, verbose: bool) -> Optional[Union[str, Dict]]:
    files = _collect_media_files(target_dir)
    if not files:
        return None

    if len(files) > 1:
        _log(f"[Facebook] ✅ Downloaded {len(files)} files → {target_dir}", verbose)
        return {
            "type": "carousel",
            "file_count": len(files),
            "files": [os.path.join(target_dir, f) for f in files],
            "path": target_dir,
        }

    file_path = os.path.join(target_dir, files[0])
    _log(f"[Facebook] ✅ Downloaded: {file_path}", verbose)
    return file_path


def download_facebook(url: str, verbose: bool = False) -> Optional[Union[str, Dict]]:
    """
    Download a Facebook video/reel or photo post at the highest available quality.

    Returns:
        str  — path to the video file (or directory, for multi-file output)
        dict — carousel metadata (files, path, etc.)
        None — every download strategy failed
    """
    _log(f"[Facebook] Processing URL: {url}", verbose)

    url = _resolve_url(url, verbose)

    target_dir = generate_target_dir("facebook")
    os.makedirs(target_dir, exist_ok=True)
    _log(f"[Facebook] Target directory: {target_dir}", verbose)

    # Tier 1: yt-dlp Python API, anonymous (best for FB video/reels)
    _log("[Facebook] Trying yt-dlp (Python API, anonymous)...", verbose)
    try:
        with yt_dlp.YoutubeDL(_build_ydl_opts(target_dir, verbose, use_cookies=False)) as ydl:
            ydl.download([url])
    except Exception as exc:
        _log(f"[Facebook] yt-dlp Python API (anonymous) error: {exc}", verbose)

    result = _finalize(target_dir, verbose)
    if result:
        return result

    # Tier 2: yt-dlp Python API, with cookies - only reached if tier 1 failed
    if _has_cookies():
        _log("[Facebook] Retrying yt-dlp (Python API, with cookies)...", verbose)
        try:
            with yt_dlp.YoutubeDL(_build_ydl_opts(target_dir, verbose, use_cookies=True)) as ydl:
                ydl.download([url])
        except Exception as exc:
            _log(f"[Facebook] yt-dlp Python API (with cookies) error: {exc}", verbose)

        result = _finalize(target_dir, verbose)
        if result:
            return result

    # Tier 3: CLI with impersonation, anonymous
    _log("[Facebook] Trying yt-dlp CLI with impersonation (anonymous)...", verbose)
    result = _download_video_cli(url, target_dir, verbose, use_cookies=False)
    if result:
        return result

    # Tier 4: CLI with impersonation, with cookies
    if _has_cookies():
        _log("[Facebook] Trying yt-dlp CLI with impersonation (with cookies)...", verbose)
        result = _download_video_cli(url, target_dir, verbose, use_cookies=True)
        if result:
            return result

    # Tier 5: gallery-dl, anonymous - fallback for photo-only posts
    _log("[Facebook] Trying gallery-dl (anonymous)...", verbose)
    files = _download_gallery_dl(url, target_dir, verbose, use_cookies=False)
    if files:
        return _finalize(target_dir, verbose)

    # Tier 6: gallery-dl, with cookies - final fallback
    if _has_cookies():
        _log("[Facebook] Retrying gallery-dl (with cookies)...", verbose)
        files = _download_gallery_dl(url, target_dir, verbose, use_cookies=True)
        if files:
            return _finalize(target_dir, verbose)

    _log("[Facebook] ❌ All download strategies failed.", verbose)
    return None
