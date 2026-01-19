import instaloader as insta
import os
import shutil
import yt_dlp

from pathlib import Path
from typing import Optional, Dict, List, Tuple

from Token import Insta_cookies, Insta_username, Insta_password

from Logic.utils.path import generate_target_dir

# Global Instaloader instance - initialized on first use
L = None

def get_instaloader():
    """Get or create Instaloader instance with optimized settings."""
    global L
    if L is None:
        L = insta.Instaloader(
            dirname_pattern='downloads/{target}',
            download_videos=True,
            download_video_thumbnails=True,  # Enable thumbnails
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
            max_connection_attempts=3,
            request_timeout=15,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    return L

def setup_session() -> bool:
    """
    Attempts to authenticate with Instagram.
    Tries session file first, falls back to username/password login.
    
    Returns:
        bool: True if authentication successful, False otherwise
    """
    L = get_instaloader()
    
    try:
        # Attempt to load existing session
        L.load_session_from_file(Insta_username, Insta_cookies)
        L.login(Insta_username, Insta_password)  # Verify login with loaded session
        
        # Verify session validity
        if L.context and hasattr(L.context, 'username') and L.context.username:
            print(f"✅ Session loaded and verified for {Insta_username}")
            return True
        else:
            print("⚠️ Session loaded but appears invalid, re-authenticating...")
            raise FileNotFoundError("Session invalid")
        
    except (FileNotFoundError, AttributeError, Exception) as e:
        print(f"🔒 Session error ({type(e).__name__}). Attempting fresh login...")
        
        # Remove corrupted session file
        session_file = f"{Insta_username}.session"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception:
                pass

        try:
            # Perform fresh login
            L.login(Insta_username, Insta_password)
            L.save_session_to_file()
            print(f"✅ Login successful! Session saved for {Insta_username}")
            return True

        except insta.exceptions.TwoFactorAuthRequiredException:
            print("🔐 Two-Factor Authentication required. Please disable 2FA or provide code.")
            return False
        except insta.exceptions.BadCredentialsException:
            print("❌ Incorrect username or password.")
            return False
        except insta.exceptions.ConnectionException as e:
            print(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected login error: {e}")
            return False

def search_instagram_profile(username: str) -> Optional[Dict]:
    """
    Search for an Instagram profile and retrieve basic information.
    
    Args:
        username: Instagram username (with or without @)
        
    Returns:
        Dict with profile info or None if not found
    """
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
    username = username.replace("@", "").strip().lower()
    
    try:
        profile = insta.Profile.from_username(L.context, username)
        
        profile_data = {
            'username': profile.username,
            'full_name': profile.full_name,
            'biography': profile.biography,
            'followers': profile.followers,
            'following': profile.followees,
            'posts_count': profile.mediacount,
            'is_private': profile.is_private,
            'is_verified': profile.is_verified,
            'profile_pic_url': profile.profile_pic_url,
            'userid': profile.userid
        }
        
        print(f"✅ Found profile: @{username}")
        return profile_data
        
    except insta.exceptions.ProfileNotExistsException:
        print(f"❌ Profile @{username} does not exist")
        return None
    except insta.exceptions.ConnectionException as e:
        print(f"❌ Connection error while searching profile: {e}")
        return None
    except Exception as e:
        print(f"❌ Error searching profile: {e}")
        return None

def get_profile_highlights(username: str) -> Optional[List[Dict]]:
    """
    Retrieve list of all highlights for a profile.
    
    Args:
        username: Instagram username
        
    Returns:
        List of highlight dictionaries with title and index, or None
    """
    if not setup_session():
        return None
    
    L = get_instaloader()
    username = username.replace("@", "").strip()
    
    try:
        profile = insta.Profile.from_username(L.context, username)
        highlights_list = list(L.get_highlights(profile))
        
        if not highlights_list:
            print(f"ℹ️ No highlights found for @{username}")
            return []
        
        highlights_info = []
        for idx, highlight in enumerate(highlights_list):
            highlights_info.append({
                'index': idx,
                'title': highlight.title,
                'item_count': highlight.itemcount
            })
        
        print(f"✅ Found {len(highlights_info)} highlight(s) for @{username}")
        return highlights_info
        
    except insta.exceptions.ProfileNotExistsException:
        print(f"❌ Profile @{username} does not exist")
        return None
    except insta.exceptions.PrivateProfileNotFollowedException:
        print(f"❌ Profile @{username} is private and you don't follow them")
        return None
    except Exception as e:
        print(f"❌ Error fetching highlights: {e}")
        return None

def download_insta_story(username: str) -> Optional[str]:
    """
    Downloads all active stories for a given username.
    
    Args:
        username: Instagram username (with or without @)
        
    Returns:
        Path to directory containing downloaded stories, or None if failed
    """
    username = username.replace("@", "").strip()
    
    # Method 2: Fallback to Instaloader
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
    
    try:
        profile =  insta.Profile.from_username(L.context, username)
        target_dir = generate_target_dir(f'story_{username}')
        os.makedirs(target_dir, exist_ok=True)
        
        story_count = 0
        
        # Download all story items
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                try:
                    L.download_storyitem(item, target=target_dir)
                    story_count += 1
                except Exception as e:
                    print(f"⚠️ Error downloading story item: {e}")
        
        if story_count == 0:

            print(f"ℹ️ No active stories found for @{username}")
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        
        # Move files from temp directory to target directory
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
        print(f"❌ Profile @{username} is private")
        return None
    except insta.exceptions.TooManyRequestsException:
        print(f"❌ Instagram rate limit hit. Please wait 10-15 minutes.")
        return None
    except Exception as e:
        print(f"❌ Story download error: {e}")
        return None

def download_insta_highlight(username: str, highlight_index: Optional[int] = None) -> Optional[str]:
    """
    Downloads Instagram highlights for a given username.
    
    Args:
        username: Instagram username
        highlight_index: Specific highlight index to download (None = all)
        
    Returns:
        Path to directory containing downloaded highlights, or None if failed
    """
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
    username = username.replace("@", "").strip()
        
    try:
        profile = insta.Profile.from_username(L.context, username)
        target_dir = generate_target_dir(f'highlight_{username}')
        os.makedirs(target_dir, exist_ok=True)
        
        highlights_count = 0
        highlights_list = list(L.get_highlights(profile))
        
        if not highlights_list:
            print(f"ℹ️ No highlights found for @{username}")
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        
        print(f"📦 Found {len(highlights_list)} highlight(s) for @{username}")
        
        # Determine which highlights to download
        if highlight_index is not None:
            if 0 <= highlight_index < len(highlights_list):
                highlights_to_download = [highlights_list[highlight_index]]
                print(f"🎯 Downloading highlight #{highlight_index + 1}: {highlights_list[highlight_index].title}")
            else:
                print(f"❌ Invalid highlight index: {highlight_index}")
                shutil.rmtree(target_dir, ignore_errors=True)
                return None
        else:
            highlights_to_download = highlights_list
            print(f"📥 Downloading all {len(highlights_list)} highlights")
        
        # Download highlight items
        for idx, highlight in enumerate(highlights_to_download):
            actual_idx = highlight_index if highlight_index is not None else idx
            try:
                print(f"⏳ Downloading: {highlight.title} ({highlight.itemcount} items)")
                
                for item in highlight.get_items():
                    try:
                        L.download_storyitem(item, target=f"{username}_highlight_{actual_idx}")
                        highlights_count += 1
                    except Exception as e:
                        print(f"⚠️ Error downloading highlight item: {e}")
                        
            except Exception as e:
                print(f"❌ Error processing highlight: {e}")
        
        if highlights_count == 0:
            print(f"❌ Failed to download any highlights")
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        
        # Move files from temp directories to target directory
        for idx in range(len(highlights_list)):
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
        print(f"❌ Highlight download error: {e}")
        return None

def download_insta_reel(url: str) -> Optional[str]:
    """
    Downloads Instagram Reels using yt_dlp.
    
    Args:
        url: Instagram reel URL
        
    Returns:
        Path to downloaded video file, or None if failed
    """
    target_dir = generate_target_dir('insta_reel')
    os.makedirs(target_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(target_dir, 'reel_%(id)s.%(ext)s'),
        'quiet': False,
        'format': 'best',
        'nocheckcertificate': True,
        'writethumbnail': True,  # Download thumbnail
    }
    
    # Add cookies if available
    if Insta_cookies and os.path.exists(Insta_cookies):
        ydl_opts['cookiefile'] = Insta_cookies
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = os.path.abspath(ydl.prepare_filename(info))
            print(f"✅ Reel downloaded successfully")
            return video_path
    except Exception as e:
        print(f"❌ Reel download error: {e}")
        shutil.rmtree(target_dir, ignore_errors=True)
        return None

def download_insta_post(url: str) -> Optional[str]:
    """
    Downloads Instagram Posts (single images, videos, or carousels) using Instaloader.
    
    Args:
        url: Instagram post URL
        
    Returns:
        Path to directory containing downloaded media, or None if failed
    """
    if not setup_session():
        print("❌ Failed to setup Instagram session")
        return None
    
    L = get_instaloader()
        
    try:
        # Extract shortcode from URL
        shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
        post = insta.Post.from_shortcode(L.context, shortcode)
        
        target_dir = generate_target_dir(f'post_{shortcode}')
        os.makedirs(target_dir, exist_ok=True)
        
        # Download post with all media
        L.download_post(post, target=shortcode)
        
        # Move files from temp directory to target directory
        source_dir = os.path.join('downloads', shortcode)
        if os.path.exists(source_dir):
            for file in os.listdir(source_dir):
                src_file = os.path.join(source_dir, file)
                dst_file = os.path.join(target_dir, file)
                shutil.move(src_file, dst_file)
            shutil.rmtree(source_dir, ignore_errors=True)
        
        print(f"✅ Post downloaded successfully")
        return target_dir if os.path.exists(target_dir) and os.listdir(target_dir) else None

    except insta.exceptions.TooManyRequestsException:
        print(f"❌ Instagram rate limit hit. Please wait 10-15 minutes.")
        return None
    except Exception as e:
        print(f"❌ Post download error: {e}")
        return None