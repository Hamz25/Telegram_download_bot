import os
import yt_dlp
from Token import Tiktok_cookies

def download_tiktok(url):
    os.makedirs('downloads', exist_ok=True)

    ydl_opts = {
        'cookiefile': Tiktok_cookies,
        'outtmpl': 'downloads/TikTok_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.tiktok.com/',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
        except Exception as e:
            print(f"TikTok Error: {e}\n\n")
            return None