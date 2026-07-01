import subprocess
import os
import urllib.request
import re
import json
import glob
import asyncio
import logging

from Logic.utils.path import generate_target_dir

logger = logging.getLogger(__name__)


def get_spotify_name(url: str) -> str:
    """
    Resolve a Spotify URL to a searchable "Artist - Title" string.

    Primary source: Spotify's public oEmbed endpoint, which returns clean
    JSON and isn't affected by page markup changes. Falls back to scraping
    the raw <title> tag (the old method) only if oEmbed is unreachable.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # Primary: oEmbed JSON - far less fragile than regex-scraping HTML
    try:
        oembed_url = f"https://open.spotify.com/oembed?url={url}"
        req = urllib.request.Request(oembed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            title = data.get('title')
            if title:
                return title
    except Exception as e:
        logger.info(f"[Spotify] oEmbed lookup failed, falling back to HTML scrape: {e}")

    # Fallback: legacy <title> tag scrape
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                title_text = title_match.group(1)
                return title_text.replace(" | Spotify", "").replace(" - song and lyrics by ", " ")
    except Exception as e:
        logger.error(f"[Spotify] HTML fallback metadata error: {e}")

    return "Unknown Song"


async def download_spotify_track(url: str, target_dir: str = None):
    if target_dir is None:
        target_dir = generate_target_dir("Spotify")

    os.makedirs(target_dir, exist_ok=True)

    search_query = get_spotify_name(url)
    logger.info(f"[Spotify] Resolved URL to search query: {search_query}")

    if search_query == "Unknown Song":
        logger.error("[Spotify] Could not resolve song details. Aborting.")
        return None

    command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", f"{target_dir}/%(title)s.%(ext)s",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--extractor-args", "youtube:player_client=android",
        f"ytsearch1:{search_query}",
    ]

    try:
        # FIXED: capture_output/text were missing, so subprocess.CalledProcessError.stderr
        # was always None - failures gave no usable diagnostic info.
        await asyncio.to_thread(
            subprocess.run, command, check=True, capture_output=True, text=True
        )

        logger.info(f"[Spotify] Success. Target dir is: {target_dir}")

        # FIXED: glob.glob() order isn't guaranteed to be newest-first - sort
        # by mtime so a stale leftover file from a prior failed run can't be
        # picked up by mistake.
        mp3_files = sorted(
            glob.glob(os.path.join(target_dir, "*.mp3")),
            key=os.path.getmtime,
            reverse=True,
        )

        if not mp3_files:
            logger.error("[Spotify] yt-dlp reported success but no mp3 file was found")
            return None

        latest_file = mp3_files[0]
        filename = os.path.basename(latest_file).replace(".mp3", "")

        if " - " in filename:
            performer, title = filename.split(" - ", 1)
        else:
            performer = "Spotify"
            title = filename

        return {
            "path": latest_file,
            "title": title.strip(),
            "performer": performer.strip(),
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"[Spotify] Download failed: {e.stderr.strip() if e.stderr else 'unknown error'}")
        return None
    except Exception as e:
        logger.error(f"[Spotify] General error: {e}")
        return None