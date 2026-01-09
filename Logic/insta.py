import instaloader as insta
import os
import shutil
import yt_dlp
from Token import Insta_cookies

INSTA_USERNAME = "electro.hstore"
SESSION_FILE = f"session-{INSTA_USERNAME}"

L = insta.Instaloader(
    dirname_pattern='downloads/{target}',
    download_videos=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)

def setup_session():
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
    setup_session()
    try:
        username = username.replace("@", "")
        profile = insta.Profile.from_username(L.context, username)
        target_dir = f"downloads/{username}"
        if os.path.exists(target_dir): shutil.rmtree(target_dir)

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
    ydl_opts = {
        'outtmpl': 'downloads/reel_%(id)s.%(ext)s',
        'quiet': True,
        'format': 'best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Reel Error: {e}")
            return None