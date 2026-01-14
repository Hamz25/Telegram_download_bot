import yt_dlp
import os
from Logic.path import generate_target_dir

def download_snapchat_video(url):
    # Create downloads folder if it doesn't exist
    target_dir = generate_target_dir('tk')
    os.makedirs(target_dir, exist_ok=True)

    ydl_opts = {
        # This tells yt-dlp where to save and what to name the file
        'outtmpl': os.path.join(target_dir, 'media_%(autonumber)03d.%(ext)s'),
        'format': 'best',
        # Snapchat sometimes blocks basic scrapers, so we use a common User-Agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Snapchat Download Error: {e}")
        return None