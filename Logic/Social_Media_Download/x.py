"""
X (Twitter) Downloader
Downloads X/Twitter videos and photo posts (single image or multi-image) at
the highest available quality.

There is no fast unofficial CDN API for X (unlike TikTok's TikWM), so the
cascade instead relies on two well-maintained scraping tools:

Strategy (in order, each one only runs if the previous one fails):
  1. gallery-dl, anonymous - best support for photo posts / image carousels.
  2. yt-dlp Python API, anonymous - best support for video tweets.
  3. yt-dlp Python API, with cookies - only if a cookie file is configured AND
     tier 2 actually failed. Cookies are never attached on a first attempt.
  4. yt-dlp CLI with --impersonate chrome, anonymous - last resort for
     video tweets blocked at the API level.
  5. yt-dlp CLI with --impersonate chrome, with cookies - final fallback.

Multi-image posts are collected from whatever gallery-dl pulls into the
target directory and returned as a carousel dict, matching tiktok.py's
carousel contract.
"""

from typing import Optional, Union, Dict, List
from urllib.parse import urlparse, urlunparse
import os
import subprocess
import yt_dlp
import requests

from Logic.utils.path import generate_target_dir

X_COOKIES: Optional[str] = os.getenv("X_cookies")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".avi")
VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif")
VALID_MEDIA_EXTENSIONS = VALID_VIDEO_EXTENSIONS + VALID_IMAGE_EXTENSIONS

REQUEST_TIMEOUT = 30
GALLERY_DL_TIMEOUT = 60


def _has_cookies() -> bool:
    return bool(X_COOKIES) and os.path.isfile(X_COOKIES)


def _log(message: str, verbose: bool = False) -> None:
    if verbose:
        print(message)


def _clean_url(url: str) -> str:
    """Strip tracking query params that aren't needed by the extractors."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _resolve_url(url: str, verbose: bool = False) -> str:
    """Resolve t.co short links to their canonical form and strip tracking params."""
    short_domains = ("t.co",)

    if any(d in url for d in short_domains):
        try:
            response = requests.head(
                url,
                allow_redirects=True,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            url = response.url
            _log(f"[X] Resolved short URL to: {url}", verbose)
        except Exception as exc:
            _log(f"[X] Could not resolve short URL ({exc}) — using original.", verbose)

    # Normalize twitter.com / mobile.twitter.com to x.com's own extractor input
    # untouched - yt-dlp and gallery-dl both handle either host, so we only
    # strip tracking params here.
    return _clean_url(url)


def _build_ydl_opts(target_dir: str, verbose: bool, use_cookies: bool = False) -> Dict:
    """yt-dlp options tuned to always pick the best available video+audio streams.
    Cookies are only attached when use_cookies=True - callers decide that based
    on whether an anonymous attempt already failed, not by default."""
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
        opts["cookiefile"] = X_COOKIES

    return opts


def _collect_media_files(target_dir: str) -> List[str]:
    return [f for f in os.listdir(target_dir) if f.lower().endswith(VALID_MEDIA_EXTENSIONS)]


def _download_gallery_dl(url: str, target_dir: str, verbose: bool = False, use_cookies: bool = False) -> List[str]:
    """Run gallery-dl anonymously (or with cookies) into target_dir. Best tool
    for X photo posts / image carousels; also picks up some videos."""
    cmd = [
        "gallery-dl",
        "--dest", target_dir,
        "-o", "filename={num:>03}_{filename}.{extension}",
        "--no-mtime",
    ]
    if use_cookies and _has_cookies():
        cmd += ["--cookies", X_COOKIES]
    cmd.append(url)

    _log(f"[X] Running gallery-dl ({'with cookies' if use_cookies else 'anonymous'}): {' '.join(cmd)}", verbose)

    try:
        subprocess.run(cmd, capture_output=not verbose, text=True, timeout=GALLERY_DL_TIMEOUT)
    except subprocess.TimeoutExpired:
        _log("[X] gallery-dl timed out", verbose)
    except FileNotFoundError:
        _log("[X] gallery-dl not found — is it installed?", verbose)
        return []
    except Exception as exc:
        _log(f"[X] gallery-dl error: {exc}", verbose)

    return _collect_media_files(target_dir)


def _download_video_cli(url: str, target_dir: str, verbose: bool = False, use_cookies: bool = False) -> Optional[str]:
    """yt-dlp CLI with browser impersonation, for when the Python API gets
    blocked. Tried anonymous first; cookies only attached when called with
    use_cookies=True (i.e. anonymous CLI already failed)."""
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
        cmd += ["--cookies", X_COOKIES]
    cmd.append(url)

    _log(f"[X] Running CLI ({'with cookies' if use_cookies else 'anonymous'}): {' '.join(cmd)}", verbose)

    try:
        subprocess.run(cmd, capture_output=not verbose, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        _log("[X] yt-dlp CLI timed out after 120s", verbose)
    except FileNotFoundError:
        _log("[X] yt-dlp CLI not found — is it installed?", verbose)
        return None
    except Exception as exc:
        _log(f"[X] yt-dlp CLI error: {exc}", verbose)

    files = _collect_media_files(target_dir)
    if not files:
        return None
    if len(files) > 1:
        _log(f"[X] ✅ CLI downloaded {len(files)} files → {target_dir}", verbose)
        return target_dir

    file_path = os.path.join(target_dir, files[0])
    _log(f"[X] ✅ CLI downloaded: {file_path}", verbose)
    return file_path


def _finalize(target_dir: str, verbose: bool) -> Optional[Union[str, Dict]]:
    """Turn whatever landed in target_dir into the tiktok.py-style return
    contract: single video path, carousel dict, or None."""
    files = _collect_media_files(target_dir)
    if not files:
        return None

    image_count = sum(1 for f in files if f.lower().endswith(VALID_IMAGE_EXTENSIONS))
    video_count = sum(1 for f in files if f.lower().endswith(VALID_VIDEO_EXTENSIONS))

    if len(files) > 1 or (image_count > 0 and video_count == 0 and image_count > 1):
        _log(f"[X] ✅ Downloaded {len(files)} files → {target_dir}", verbose)
        return {
            "type": "carousel",
            "file_count": len(files),
            "files": [os.path.join(target_dir, f) for f in files],
            "path": target_dir,
        }

    file_path = os.path.join(target_dir, files[0])
    _log(f"[X] ✅ Downloaded: {file_path}", verbose)
    return file_path


def download_x(url: str, verbose: bool = False) -> Optional[Union[str, Dict]]:
    """
    Download an X (Twitter) video or photo post at the highest available quality.

    Returns:
        str  — path to the video file (or directory, for multi-file output)
        dict — carousel metadata (files, path, etc.)
        None — every download strategy failed
    """
    _log(f"[X] Processing URL: {url}", verbose)

    url = _resolve_url(url, verbose)

    target_dir = generate_target_dir("x")
    os.makedirs(target_dir, exist_ok=True)
    _log(f"[X] Target directory: {target_dir}", verbose)

    # Tier 1: gallery-dl, anonymous (best for photo posts / carousels)
    _log("[X] Trying gallery-dl (anonymous)...", verbose)
    files = _download_gallery_dl(url, target_dir, verbose, use_cookies=False)
    if files:
        return _finalize(target_dir, verbose)

    # Tier 2: yt-dlp Python API, anonymous (best for video tweets)
    _log("[X] Trying yt-dlp (Python API, anonymous)...", verbose)
    try:
        with yt_dlp.YoutubeDL(_build_ydl_opts(target_dir, verbose, use_cookies=False)) as ydl:
            ydl.download([url])
    except Exception as exc:
        _log(f"[X] yt-dlp Python API (anonymous) error: {exc}", verbose)

    result = _finalize(target_dir, verbose)
    if result:
        return result

    # Tier 3: yt-dlp Python API, with cookies - only reached if tier 2 failed
    if _has_cookies():
        _log("[X] Retrying yt-dlp (Python API, with cookies)...", verbose)
        try:
            with yt_dlp.YoutubeDL(_build_ydl_opts(target_dir, verbose, use_cookies=True)) as ydl:
                ydl.download([url])
        except Exception as exc:
            _log(f"[X] yt-dlp Python API (with cookies) error: {exc}", verbose)

        result = _finalize(target_dir, verbose)
        if result:
            return result

    # Tier 4: gallery-dl retry with cookies, in case tier 1 only failed due to auth
    if _has_cookies():
        _log("[X] Retrying gallery-dl (with cookies)...", verbose)
        files = _download_gallery_dl(url, target_dir, verbose, use_cookies=True)
        if files:
            return _finalize(target_dir, verbose)

    # Tier 5: CLI with impersonation, anonymous
    _log("[X] Trying yt-dlp CLI with impersonation (anonymous)...", verbose)
    result = _download_video_cli(url, target_dir, verbose, use_cookies=False)
    if result:
        return result

    # Tier 6: CLI with impersonation, with cookies - final fallback
    if _has_cookies():
        _log("[X] Trying yt-dlp CLI with impersonation (with cookies)...", verbose)
        result = _download_video_cli(url, target_dir, verbose, use_cookies=True)
        if result:
            return result

    _log("[X] ❌ All download strategies failed.", verbose)
    return None
