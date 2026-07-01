"""
TikTok Downloader
Downloads TikTok videos and photo carousels at the highest available quality.

Video strategy (in order, each one only runs if the previous one fails):
  1. TikWM direct CDN URL (hdplay, then play) - fastest, bypasses TikTok IP blocks.
  2. yt-dlp Python API, anonymous - used when TikWM is unreachable or its URLs fail.
  3. yt-dlp Python API, with cookies - only if a cookie file is configured AND
     tier 2 actually failed. Cookies are never attached on a first attempt.
  4. yt-dlp CLI with --impersonate chrome, anonymous - last resort.
  5. yt-dlp CLI with --impersonate chrome, with cookies - final fallback.

Carousels (photo posts) are downloaded directly from TikWM image URLs.
"""

from typing import Optional, Union, Dict, List
from urllib.parse import urlparse, urlunparse
import os
import subprocess
import yt_dlp
import requests

from Logic.utils.path import generate_target_dir

TIKTOK_COOKIES: Optional[str] = os.getenv("Tiktok_cookies")

# Multiple mirrors so a single blocked/down endpoint doesn't kill the request
TIKWM_API_MIRRORS = [
    "https://www.tikwm.com/api/",
    "https://tikwm.com/api/",
]
TIKWM_API_PARAMS = {"count": 12, "cursor": 0, "web": 1, "hd": 1}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".avi")
VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".heic")
VALID_MEDIA_EXTENSIONS = VALID_VIDEO_EXTENSIONS + VALID_IMAGE_EXTENSIONS

REQUEST_TIMEOUT = 30
CHUNK_SIZE = 8192


def _has_cookies() -> bool:
    return bool(TIKTOK_COOKIES) and os.path.isfile(TIKTOK_COOKIES)


def _log(message: str, verbose: bool = False) -> None:
    if verbose:
        print(message)


def _clean_url(url: str) -> str:
    """Strip tracking query params (e.g. _r, _t) that break TikWM's parser."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _resolve_url(url: str, verbose: bool = False) -> str:
    """Resolve vt./vm. short links to their canonical form and strip tracking params."""
    short_domains = ("vt.tiktok.com", "vm.tiktok.com")

    if any(d in url for d in short_domains):
        try:
            response = requests.head(
                url,
                allow_redirects=True,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            url = response.url
            _log(f"[TikTok] Resolved short URL to: {url}", verbose)
        except Exception as exc:
            _log(f"[TikTok] Could not resolve short URL ({exc}) — using original.", verbose)

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
        opts["cookiefile"] = TIKTOK_COOKIES

    return opts


def _collect_media_files(target_dir: str) -> List[str]:
    return [f for f in os.listdir(target_dir) if f.lower().endswith(VALID_MEDIA_EXTENSIONS)]


def _stream_to_file(url: str, filepath: str) -> bool:
    """
    Stream url to filepath. Validates the response is actually media (not an
    error page) before keeping it, since CDNs sometimes return HTTP 200 with
    an HTML/JSON error body.
    """
    response = requests.get(
        url, stream=True, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
    )
    content_type = response.headers.get("Content-Type", "")

    if response.status_code != 200 or not content_type.startswith(("video", "image")):
        return False

    with open(filepath, "wb") as fh:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            fh.write(chunk)

    if os.path.getsize(filepath) == 0:
        os.remove(filepath)
        return False

    return True


def _download_carousel(post_data: Dict, target_dir: str, verbose: bool = False) -> Optional[Dict]:
    """Download every image in a TikTok photo carousel via TikWM image URLs."""
    _log("[TikTok] Downloading carousel...", verbose)

    image_urls: List[str] = post_data.get("images", [])
    downloaded_files: List[str] = []

    for idx, img_url in enumerate(image_urls, 1):
        try:
            filepath = os.path.join(target_dir, f"media_{idx:03d}.jpg")
            if _stream_to_file(img_url, filepath):
                downloaded_files.append(filepath)
                _log(f"  ✅ Image {idx}/{len(image_urls)} downloaded", verbose)
            else:
                _log(f"  ⚠️  Image {idx} failed", verbose)
        except Exception as exc:
            _log(f"  ⚠️  Image {idx} error: {exc}", verbose)

    if not downloaded_files:
        _log("[TikTok] No carousel images downloaded", verbose)
        return None

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


def _download_video_cli(url: str, target_dir: str, verbose: bool = False, use_cookies: bool = False) -> Optional[str]:
    """yt-dlp CLI with browser impersonation, which gets past TikTok IP blocks
    the Python API can't avoid. Tried anonymous first; cookies only attached
    when called with use_cookies=True (i.e. anonymous CLI already failed)."""
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
        cmd += ["--cookies", TIKTOK_COOKIES]
    cmd.append(url)

    _log(f"[TikTok] Running CLI ({'with cookies' if use_cookies else 'anonymous'}): {' '.join(cmd)}", verbose)

    try:
        subprocess.run(cmd, capture_output=not verbose, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        _log("[TikTok] yt-dlp CLI timed out after 120s", verbose)
    except FileNotFoundError:
        _log("[TikTok] yt-dlp CLI not found — is it installed?", verbose)
        return None
    except Exception as exc:
        _log(f"[TikTok] yt-dlp CLI error: {exc}", verbose)

    files = _collect_media_files(target_dir)
    if not files:
        return None
    if len(files) > 1:
        _log(f"[TikTok] ✅ CLI downloaded {len(files)} files → {target_dir}", verbose)
        return target_dir

    file_path = os.path.join(target_dir, files[0])
    _log(f"[TikTok] ✅ CLI downloaded: {file_path}", verbose)
    return file_path


def _download_video(
    url: str, target_dir: str, verbose: bool = False, post_data: Optional[Dict] = None,
) -> Optional[str]:
    """
    Download a TikTok video, trying highest-quality / least-invasive sources first:
      1. TikWM direct CDN URL (hdplay, then play) - no cookies, ever
      2. yt-dlp Python API, anonymous
      3. yt-dlp Python API, with cookies (only if tier 2 failed and cookies exist)
      4. yt-dlp CLI with --impersonate chrome, anonymous
      5. yt-dlp CLI with --impersonate chrome, with cookies (only if tier 4 failed and cookies exist)
    """
    _log("[TikTok] Downloading video...", verbose)

    if post_data:
        for quality_key in ("hdplay", "play"):
            video_url = post_data.get(quality_key)
            if not video_url:
                continue

            # TikWM sometimes returns a relative path (no scheme/domain) -
            # this was silently failing every request and wasting the
            # fastest tier before falling through to yt-dlp.
            if video_url.startswith("/"):
                video_url = f"https://www.tikwm.com{video_url}"

            filepath = os.path.join(target_dir, "media_001.mp4")
            try:
                if _stream_to_file(video_url, filepath):
                    _log(f"[TikTok] ✅ Downloaded via TikWM ({quality_key}): {filepath}", verbose)
                    return filepath
            except Exception as exc:
                _log(f"[TikTok] TikWM {quality_key} error: {exc}", verbose)

        _log("[TikTok] TikWM direct URLs failed — falling back to yt-dlp.", verbose)

    # Tier 2: yt-dlp Python API, anonymous
    _log("[TikTok] Downloading with yt-dlp (Python API, anonymous)...", verbose)
    try:
        with yt_dlp.YoutubeDL(_build_ydl_opts(target_dir, verbose, use_cookies=False)) as ydl:
            ydl.download([url])
    except Exception as exc:
        _log(f"[TikTok] yt-dlp Python API (anonymous) error: {exc}", verbose)

    files = _collect_media_files(target_dir)
    if files:
        if len(files) > 1:
            _log(f"[TikTok] ✅ Downloaded {len(files)} files → {target_dir}", verbose)
            return target_dir
        file_path = os.path.join(target_dir, files[0])
        _log(f"[TikTok] ✅ Downloaded: {file_path}", verbose)
        return file_path

    # Tier 3: yt-dlp Python API, with cookies - only reached if tier 2 failed
    if _has_cookies():
        _log("[TikTok] Retrying yt-dlp (Python API, with cookies)...", verbose)
        try:
            with yt_dlp.YoutubeDL(_build_ydl_opts(target_dir, verbose, use_cookies=True)) as ydl:
                ydl.download([url])
        except Exception as exc:
            _log(f"[TikTok] yt-dlp Python API (with cookies) error: {exc}", verbose)

        files = _collect_media_files(target_dir)
        if files:
            if len(files) > 1:
                _log(f"[TikTok] ✅ Downloaded {len(files)} files → {target_dir}", verbose)
                return target_dir
            file_path = os.path.join(target_dir, files[0])
            _log(f"[TikTok] ✅ Downloaded: {file_path}", verbose)
            return file_path

    # Tier 4: CLI with impersonation, anonymous
    _log("[TikTok] Trying yt-dlp CLI with impersonation (anonymous)...", verbose)
    result = _download_video_cli(url, target_dir, verbose, use_cookies=False)
    if result:
        return result

    # Tier 5: CLI with impersonation, with cookies - final fallback
    if _has_cookies():
        _log("[TikTok] Trying yt-dlp CLI with impersonation (with cookies)...", verbose)
        result = _download_video_cli(url, target_dir, verbose, use_cookies=True)
        if result:
            return result

    _log("[TikTok] ❌ All download strategies failed.", verbose)
    return None


def _query_tikwm(url: str, verbose: bool = False) -> Optional[Dict]:
    """Query TikWM API mirrors in order until one returns valid post data."""
    for mirror in TIKWM_API_MIRRORS:
        try:
            response = requests.post(
                mirror,
                data={**TIKWM_API_PARAMS, "url": url},
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code != 200:
                continue

            data = response.json()
            if data.get("code") != 0:
                _log(f"[TikTok] {mirror} error: {data.get('msg', 'Unknown')}", verbose)
                continue

            return data["data"]

        except requests.exceptions.RequestException as exc:
            _log(f"[TikTok] {mirror} unreachable ({exc})", verbose)
            continue

    _log("[TikTok] All TikWM mirrors failed — falling back to yt-dlp.", verbose)
    return None


def download_tiktok(url: str, verbose: bool = False) -> Optional[Union[str, Dict]]:
    """
    Download a TikTok video or photo carousel at the highest available quality.

    Returns:
        str  — path to the video file (or directory, for multi-file output)
        dict — carousel metadata (files, path, etc.)
        None — every download strategy failed
    """
    _log(f"[TikTok] Processing URL: {url}", verbose)

    url = _resolve_url(url, verbose)

    target_dir = generate_target_dir("tiktok")
    os.makedirs(target_dir, exist_ok=True)
    _log(f"[TikTok] Target directory: {target_dir}", verbose)

    try:
        post_data = _query_tikwm(url, verbose)
    except Exception as exc:
        _log(f"[TikTok] Unexpected error during API query: {exc}", verbose)
        return None

    if post_data is None:
        return _download_video(url, target_dir, verbose)

    if post_data.get("images"):
        _log("[TikTok] Content type: Photo carousel", verbose)
        return _download_carousel(post_data, target_dir, verbose)

    _log("[TikTok] Content type: Video", verbose)
    return _download_video(url, target_dir, verbose, post_data=post_data)