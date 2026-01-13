import instaloader as insta
import os
import shutil
import yt_dlp
import http.cookiejar
from Token import Insta_cookies, Insta_username, Insta_password

# Initialize Instaloader for Stories and Posts
L = insta.Instaloader(
    dirname_pattern='downloads/{target}',
    download_videos=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)

def setup_session():
    """Attempts login via session file, falling back to Username/Password."""
    try:
        # 1. Always try the session file first to avoid over-logging in
        L.load_session_from_file(Insta_username)
        print(f"✅ Session loaded from file. User: {L.test_login()}")
        
    except FileNotFoundError:
        print(f"🔑 No session file found. Logging in as {Insta_username}...")
        try:
            # 2. Standard Login
            L.login(Insta_username, Insta_password)
            
            # 3. Save the session immediately so we don't need the password next time
            L.save_session_to_file()
            print(f"✅ Login successful! Session saved for {L.test_login()}")

        except insta.exceptions.TwoFactorAuthRequiredException:
            # 4. Handle 2FA if enabled on your account
            print("🔐 Two-Factor Authentication required.")
            two_factor_code = input("Enter the 2FA code sent to your device: ")
            try:
                L.two_factor_login(two_factor_code)
                L.save_session_to_file()
                print("✅ 2FA Login successful!")
            except Exception as e:
                print(f"❌ 2FA Login failed: {e}")

        except insta.exceptions.BadCredentialsException:
            print("❌ Incorrect username or password.")
        except insta.exceptions.ConnectionException as e:
            print(f"❌ Connection error (Instagram might be blocking your IP): {e}")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

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
        target_name = f"post_{shortcode}"
        # Use absolute path for the specific post folder
        target_dir = os.path.abspath(f"downloads/",target_name)
        
        if os.path.exists(target_dir): 
            shutil.rmtree(target_dir)

        # download_post handles multiple images (carousels)
        L.download_post(post, target=target_dir)
        if os.path.exists:
            return target_dir 
        return None
        
    except Exception as e:
        print(f"Insta Post Error: {e}")
        return None