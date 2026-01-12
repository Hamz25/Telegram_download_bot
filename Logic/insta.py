import instaloader as insta
import os
import shutil
import yt_dlp
from Token import Insta_cookies

INSTA_USERNAME = "Put Your fake insta account username here"
SESSION_FILE = f"session-{INSTA_USERNAME}"

# Initialize Instaloader for Stories and Posts
L = insta.Instaloader(
    dirname_pattern='downloads/{target}',
    download_videos=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)

def setup_session():
    """Loads session from file or cookie file to avoid login blocks."""
    try:
        L.load_session_from_file(INSTA_USERNAME, filename=SESSION_FILE)
    except FileNotFoundError:
        if os.path.exists(Insta_cookies):
            print(f"DEBUG: Loading cookies from {Insta_cookies}")
            L.context.load_cookies_from_file(Insta_cookies)
            L.save_session_to_file(filename=SESSION_FILE)
        else:
            print("DEBUG ERROR: No cookie file found at the specified path.")

def download_insta_story(username):
    """Downloads all active stories for a given username."""
    setup_session()
    try:
        username = username.replace("@", "")
        profile = insta.Profile.from_username(L.context, username)
        # Use absolute path for reliability
        target_dir = os.path.abspath(f"downloads/{username}") 
        
        if os.path.exists(target_dir): 
            shutil.rmtree(target_dir)

        has_stories = False
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                L.download_storyitem(item, target=target_dir)
                has_stories = True
        return target_dir if has_stories else None
    except Exception as e:
        print(f"Insta Story Error: {e}")
        return None

def download_insta_reel(url):
    """Downloads Instagram Reels using yt_dlp."""
    download_folder = os.path.abspath('downloads')
    os.makedirs(download_folder, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(download_folder, 'reel_%(id)s.%(ext)s'),
        'quiet': True,
        'format': 'best',
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            # Convert to absolute path to prevent 'File Not Found' in Uploader
            return os.path.abspath(ydl.prepare_filename(info))
        except Exception as e:
            print(f"Reel Error: {e}")
            return None

def download_insta_post(url):
    """Downloads Instagram Posts (Images/Carousels) using Instaloader."""
    setup_session()
    try:
        # Extract shortcode from URL (e.g., /p/SHORTCODE/)
        shortcode = url.split("/")[-2] 
        post = insta.Post.from_shortcode(L.context, shortcode)
        
        # Use absolute path for the specific post folder
        target_dir = os.path.abspath(f"downloads/post_{shortcode}")
        
        if os.path.exists(target_dir): 
            shutil.rmtree(target_dir)

        # download_post handles multiple images (carousels)
        L.download_post(post, target=target_dir)
        return target_dir 
    except Exception as e:
        print(f"Insta Post Error: {e}")
        return None