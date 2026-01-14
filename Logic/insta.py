import instaloader as insta
import uuid
import os
import shutil
import yt_dlp
import time
import http.cookiejar
from Token import Insta_cookies, Insta_username, Insta_password
from Logic.path import generate_target_dir

# Global Instaloader instance - will be initialized on first use
L = None

def get_instaloader():
    """Get or create Instaloader instance."""
    global L
    if L is None:
        L = insta.Instaloader(
            dirname_pattern='downloads/{target}',
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
            max_connection_attempts=3,
            request_timeout=10,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
    return L

def setup_session():
    """Attempts login via session file, falling back to Username/Password."""
    L = get_instaloader()
    
    try:
        # Try loading session
        L.load_session_from_file(Insta_username)
        
        # Test if session is valid by checking context
        if L.context and hasattr(L.context, 'username') and L.context.username:
            print(f"✅ Session loaded and verified for {Insta_username}")
            return True
        else:
            print(f"⚠️ Session loaded but appears invalid, re-logging in...")
            raise FileNotFoundError("Session invalid")
        
    except (FileNotFoundError, AttributeError, Exception) as e:
        print(f"🔒 Session error ({e}). Logging in as {Insta_username}...")
        
        # Delete corrupted session file
        try:
            session_file = f"{Insta_username}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
        except:
            pass
        
        try:
            # Fresh login
            L.login(Insta_username, Insta_password)
            L.save_session_to_file()
            print(f"✅ Login successful! Session saved for {Insta_username}")
            return True

        except insta.exceptions.TwoFactorAuthRequiredException:
            print("🔐 Two-Factor Authentication required.")

        except insta.exceptions.BadCredentialsException:
            print("❌ Incorrect username or password.")
            return False
        except insta.exceptions.ConnectionException as e:
            print(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            return False

def download_insta_story(username):
    """Downloads all active stories for a given username."""
    username = username.replace("@", "").strip()
    
    # Try yt-dlp with cookies first
    if Insta_cookies and os.path.exists(Insta_cookies):
        try:
            print(f"Attempting to download stories for @{username} using yt-dlp with cookies...")
            target_dir = generate_target_dir(f'story_{username}')
            os.makedirs(target_dir, exist_ok=True)
            
            url = f"https://www.instagram.com/stories/{username}/"
            
            ydl_opts = {
                'outtmpl': os.path.join(target_dir, 'story_%(autonumber)03d.%(ext)s'),
                'quiet': False,
                'format': 'best',
                'nocheckcertificate': True,
                'cookiefile': Insta_cookies,  # Use cookies for authentication
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    
                    # Check if any files were downloaded
                    files = [f for f in os.listdir(target_dir) 
                            if f.lower().endswith(('.mp4', '.jpg', '.jpeg', '.png', '.webp'))]
                    
                    if files:
                        print(f"✅ Downloaded {len(files)} stories using yt-dlp")
                        return target_dir
                    else:
                        print("No stories found with yt-dlp, trying Instaloader...")
                        shutil.rmtree(target_dir, ignore_errors=True)
                        
                except Exception as e:
                    print(f"yt-dlp failed: {e}")
                    shutil.rmtree(target_dir, ignore_errors=True)
        
        except Exception as e:
            print(f"yt-dlp error: {e}")
    else:
        print("No cookies file found, skipping yt-dlp method...")
    
    # Fallback to Instaloader
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
    
    try:
        profile = insta.Profile.from_username(L.context, username)
        target_dir = generate_target_dir(f'story_{username}')
        os.makedirs(target_dir, exist_ok=True)
        
        story_count = 0
        
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                try:
                    L.download_storyitem(item, target=username)
                    story_count += 1
                    time.sleep(2)  # Add delay between downloads
                except Exception as e:
                    print(f"Error downloading story item: {e}")
        
        if story_count == 0:
            print(f"No active stories found for @{username}")
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        
        # Move files
        source_dir = os.path.join('downloads', username)
        if os.path.exists(source_dir):
            for file in os.listdir(source_dir):
                src_file = os.path.join(source_dir, file)
                dst_file = os.path.join(target_dir, file)
                shutil.move(src_file, dst_file)
            shutil.rmtree(source_dir, ignore_errors=True)
        
        print(f"✅ Downloaded {story_count} stories from @{username}")
        return target_dir if os.path.exists(target_dir) and os.listdir(target_dir) else None
        
    except insta.exceptions.ProfileNotExistsException:
        print(f"❌ Profile @{username} does not exist")
        return None
    except insta.exceptions.PrivateProfileNotFollowedException:
        print(f"❌ Profile @{username} is private and you don't follow them")
        return None
    except insta.exceptions.TooManyRequestsException:
        print(f"❌ Instagram rate limit hit. Please wait 10-15 minutes.")
        return None
    except Exception as e:
        print(f"Insta Story Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def download_insta_highlight(username, highlight_index=None):
    """Downloads Instagram highlights for a given username."""
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
        
    try:
        username = username.replace("@", "").strip()
        profile = insta.Profile.from_username(L.context, username)
        
        target_dir = generate_target_dir(f'highlight_{username}')
        os.makedirs(target_dir, exist_ok=True)
        
        highlights_count = 0
        highlights_list = list(L.get_highlights(profile))
        
        if not highlights_list:
            print(f"No highlights found for @{username}")
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        
        print(f"Found {len(highlights_list)} highlight(s) for @{username}")
        
        if highlight_index is not None:
            if 0 <= highlight_index < len(highlights_list):
                highlights_to_download = [highlights_list[highlight_index]]
            else:
                print(f"❌ Invalid highlight index: {highlight_index}")
                return None
        else:
            highlights_to_download = highlights_list
        
        for idx, highlight in enumerate(highlights_to_download):
            try:
                print(f"Downloading highlight: {highlight.title}")
                
                for item in highlight.get_items():
                    try:
                        L.download_storyitem(item, target=f"{username}_highlight_{idx}")
                        highlights_count += 1
                        time.sleep(2)  # Add delay
                    except Exception as e:
                        print(f"Error downloading highlight item: {e}")
                        
            except Exception as e:
                print(f"Error processing highlight {idx}: {e}")
        
        if highlights_count == 0:
            print(f"Failed to download any highlights")
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        
        # Move files
        for idx in range(len(highlights_to_download)):
            source_dir = os.path.join('downloads', f"{username}_highlight_{idx}")
            if os.path.exists(source_dir):
                for file in os.listdir(source_dir):
                    src_file = os.path.join(source_dir, file)
                    dst_file = os.path.join(target_dir, file)
                    shutil.move(src_file, dst_file)
                shutil.rmtree(source_dir, ignore_errors=True)
        
        print(f"✅ Downloaded {highlights_count} items from highlights")
        return target_dir if os.path.exists(target_dir) and os.listdir(target_dir) else None
        
    except insta.exceptions.ProfileNotExistsException:
        print(f"❌ Profile @{username} does not exist")
        return None
    except insta.exceptions.PrivateProfileNotFollowedException:
        print(f"❌ Profile @{username} is private and you don't follow them")
        return None
    except insta.exceptions.TooManyRequestsException:
        print(f"❌ Instagram rate limit hit. Please wait 10-15 minutes.")
        return None
    except Exception as e:
        print(f"Insta Highlight Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def download_insta_reel(url):
    """Downloads Instagram Reels using yt_dlp."""
    target_dir = generate_target_dir('insta_reel')
    os.makedirs(target_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(target_dir, 'reel_%(id)s.%(ext)s'),
        'quiet': True,
        'format': 'best',
        'nocheckcertificate': True,
    }
    
    # Add cookies if available
    if Insta_cookies and os.path.exists(Insta_cookies):
        ydl_opts['cookiefile'] = Insta_cookies
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return os.path.abspath(ydl.prepare_filename(info))
        except Exception as e:
            print(f"Reel Error: {e}")
            return None

def download_insta_post(url):
    """Downloads Instagram Posts (Images/Carousels) using Instaloader."""
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
        
    try:
        shortcode = url.split("/")[-2] 
        post = insta.Post.from_shortcode(L.context, shortcode)
        
        target_dir = generate_target_dir('post_' + shortcode)
        os.makedirs(target_dir, exist_ok=True)
        
        L.download_post(post, target=shortcode)
        time.sleep(2)  # Add delay
        
        # Move files
        source_dir = os.path.join('downloads', shortcode)
        if os.path.exists(source_dir):
            for file in os.listdir(source_dir):
                src_file = os.path.join(source_dir, file)
                dst_file = os.path.join(target_dir, file)
                shutil.move(src_file, dst_file)
            shutil.rmtree(source_dir, ignore_errors=True)
        
        return target_dir if os.path.exists(target_dir) and os.listdir(target_dir) else None

    except insta.exceptions.TooManyRequestsException:
        print(f"❌ Instagram rate limit hit. Please wait 10-15 minutes.")
        return None
    except Exception as e:
        print(f"Insta Post Error: {e}")
        return None