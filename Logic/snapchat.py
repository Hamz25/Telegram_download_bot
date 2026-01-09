import yt_dlp
import os

def download_snapchat_video(url):
    # Create downloads folder if it doesn't exist
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        # This tells yt-dlp where to save and what to name the file
        'outtmpl': 'downloads/snapchat_%(id)s.%(ext)s',
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