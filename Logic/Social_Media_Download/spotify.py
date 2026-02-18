import subprocess
from Logic.utils.path import generate_target_dir
import os
import urllib.request
import re
import glob
import asyncio
# from Token import Youtube_cookes # Commented out to prevent 403 Errors

def get_spotify_name(url):
    try:
        # 1. Pretend to be a browser to avoid getting blocked
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # 2. Look for the <title> tag in the HTML
            title_match = re.search(r'<title>(.*?)</title>', html)
            
            if title_match:
                title_text = title_match.group(1)
                # Clean up the string for YouTube search
                clean_title = title_text.replace(" | Spotify", "").replace(" - song and lyrics by ", " ")
                return clean_title
    except Exception as e:
        print(f"Metadata error: {e}")
    return "Unknown Song"

async def download_spotify_track(url: str, target_dir: str = None):
    # Use generate_target_dir if no path provided to ensure unique folder
    if target_dir is None:
        target_dir = generate_target_dir("Spotify")

    # Ensure directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # 1. Get the actual song name from the URL
    try:
        search_query = get_spotify_name(url)
        print(f"[Spotify] Resolved URL to search query: {search_query}")

        if search_query == "Unknown Song":
            print("Could not find song details. Aborting.")
            return None


        command = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--output", f"{target_dir}/%(title)s.%(ext)s",
            "--no-playlist",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "--extractor-args", "youtube:player_client=android",
            f"ytsearch1:{search_query}"
        ]

        # Run in thread so bot doesn't freeze
        await asyncio.to_thread(subprocess.run, command, check=True)
            
        print(f"[Spotify]: Success. Target dir is: {target_dir}")
        
        # 3. Find the downloaded file
        mp3_files = glob.glob(os.path.join(target_dir, "*.mp3"))
        
        if not mp3_files:
            return None

        latest_file = mp3_files[0]
        filename = os.path.basename(latest_file).replace(".mp3", "")

        # 4. Extract Performer and Title from filename (if possible)
        if " - " in filename:
            performer, title = filename.split(" - ", 1)
        else:
            performer = "Spotify"
            title = filename

        # 5. Return the result
        return {
            "path": latest_file, 
            "title": title.strip(), 
            "performer": performer.strip() 
        }

    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")
        return None
    except Exception as e:
        print(f"General Error: {e}")
        return None