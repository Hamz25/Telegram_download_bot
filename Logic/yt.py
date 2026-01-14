import yt_dlp
import os
import uuid
from Logic.path import generate_target_dir
def get_video_info(url): #this function will extract the video information without downloading
    ydl_opts = {'noplaylist': True, 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail')
            video_duration = info.get('duration', 0)
            size = info.get('filesize') or info.get('filesize_approx') or 0
            is_short = 'shorts' in url or video_duration < 60
            
            return info, is_short, size, title, thumbnail, video_duration
        except Exception as e:
            print(f"Error fetching video info: {e}")
            return None, False, 0, "Unknown Title", None, 0

def download_youtube(url, quality='720', is_audio=False):
    """Downloads YouTube media and returns the raw converted thumbnail."""
    #create a file
    target_dir = generate_target_dir("yt_")
    os.makedirs(target_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': target_dir + '/%(title)s.%(ext)s', 
        'noplaylist': True,
        'writethumbnail': is_audio,
    }

    if is_audio:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegThumbnailsConvertor',
                    'format': 'jpg',
                    'when': 'before_dl'
                },
            ],
        })
    else:
        ydl_opts['format'] = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        if is_audio:
            # Path to the converted .mp3
            final_path = filename.rsplit('.', 1)[0] + ".mp3"
            # Path to the raw .jpg thumbnail converted by FFmpegThumbnailsConvertor
            thumb_path = filename.rsplit('.', 1)[0] + ".jpg"
            
            if not os.path.exists(thumb_path):
                thumb_path = None

            return {
                "path": final_path,
                "title": info.get('title', 'Unknown Title'),
                "performer": info.get('uploader', 'Unknown Artist'),
                "thumb": thumb_path,
                "folder": target_dir
            }
        else:
            return {"path": filename}