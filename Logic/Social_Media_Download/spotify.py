"""
Spotify Track Downloader
Module for downloading Spotify tracks as MP3 audio files.
Uses spotdl command-line utility for reliable track extraction and conversion.

Dependencies:
    - spotdl: Command-line tool for downloading Spotify tracks
    - ffmpeg: Audio encoding and format conversion (required by spotdl)
"""

from typing import Optional, Dict
import os
import subprocess
import glob

from Logic.utils.path import generate_target_dir

# ============================================================================
# Constants
# ============================================================================

# spotdl download format
SPOTIFY_DOWNLOAD_FORMAT = "mp3"

# Artist-Title separator used by spotdl
ARTIST_TITLE_SEPARATOR = " - "

# spotdl command
SPOTDL_COMMAND = ["spotdl", "download"]

# ============================================================================
# Download Functions
# ============================================================================


def download_spotify_track(url: str) -> Optional[Dict[str, str]]:
    """
    Download a Spotify track as an MP3 audio file.

    Uses spotdl utility to download and convert Spotify tracks to MP3 format
    with metadata automatically embedded.

    Args:
        url: Spotify track URL or URI (e.g., https://open.spotify.com/track/...)

    Returns:
        Optional[Dict[str, str]]: Dictionary with track information or None on failure
            Keys:
            - 'path': Full file path to downloaded MP3
            - 'title': Track title
            - 'performer': Artist name
            - 'thumb': Thumbnail/cover art (currently None as metadata embedded)

    Example:
        >>> result = download_spotify_track("https://open.spotify.com/track/...")
        >>> if result:
        ...     print(f"Title: {result['title']}")
        ...     print(f"Artist: {result['performer']}")
        ...     print(f"File: {result['path']}")

    Note:
        Requires spotdl and ffmpeg to be installed and in system PATH
    """
    try:
        # Create unique download directory
        download_path = generate_target_dir("spotify")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        print(f"[Spotify] Downloading to: {download_path}")
        print(f"[Spotify] URL: {url}")

        # Run spotdl command to download track
        command = [
            *SPOTDL_COMMAND,
            url,
            "--output",
            download_path,
            "--format",
            SPOTIFY_DOWNLOAD_FORMAT,
        ]

        print(f"[Spotify] Executing: {' '.join(command)}")

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

        print(f"[Spotify] Command output: {result.stdout}")

        # Find the downloaded MP3 file (most recently created)
        mp3_files = glob.glob(f"{download_path}/*.mp3")

        if not mp3_files:
            print(f"[Spotify] ❌ No MP3 file found after download")
            return None

        # Get the most recently created MP3
        latest_file = max(mp3_files, key=os.path.getctime)
        filename_without_ext = os.path.basename(latest_file).replace(
            f".{SPOTIFY_DOWNLOAD_FORMAT}", ""
        )

        print(f"[Spotify] Found file: {latest_file}")

        # Parse artist and title from filename
        # spotdl default format is "Artist - Song Name"
        if ARTIST_TITLE_SEPARATOR in filename_without_ext:
            performer, title = filename_without_ext.split(
                ARTIST_TITLE_SEPARATOR, 1
            )
        else:
            performer = "Unknown Artist"
            title = filename_without_ext

        print(f"[Spotify] ✅ Download successful")
        print(f"[Spotify] Artist: {performer} | Title: {title}")

        return {
            "path": latest_file,
            "title": title,
            "performer": performer,
            "thumb": None,  # Metadata already embedded in MP3
        }

    except FileNotFoundError as e:
        print(f"[Spotify] ❌ spotdl command not found: {e}")
        print(
            "[Spotify] Make sure spotdl is installed: "
            "pip install spotdl"
        )
        return None

    except subprocess.CalledProcessError as e:
        print(f"[Spotify] ❌ spotdl process failed: {e}")
        print(f"[Spotify] Error output: {e.stderr}")
        return None

    except Exception as e:
        print(f"[Spotify] ❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return None