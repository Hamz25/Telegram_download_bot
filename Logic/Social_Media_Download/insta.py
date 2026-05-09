import os
import subprocess
import asyncio
import instaloader
from typing import Optional, Dict, List
from Token import Insta_cookies 
from Logic.utils.path import generate_target_dir

# Initialize Instaloader API
L = instaloader.Instaloader(max_connection_attempts=1)

# Set a mobile User Agent to help bypass network restrictions
L.context.user_agent = "Instagram 150.0.0.33.120 Android (24/7.0; 480dpi; 1080x1920; Samsung; SM-G930F; herolte; samsungexynos8890; en_US)"

if Insta_cookies and os.path.exists(Insta_cookies):
    # Use the session file you generated
    L.load_session_from_file("electro.hstore", filename=Insta_cookies)
    
async def _run_instaloader(args: list, target_dir: str) -> Optional[str]:
    session_args = ["--sessionfile", Insta_cookies] if os.path.exists(Insta_cookies) else []

    base_command = [
        "instaloader",
        "--dirname-pattern", target_dir,
        "--filename-pattern", "{shortcode}",
        "--no-metadata-json",
        "--no-compress-json",
        "--no-captions",
        "--no-profile-pic",
        "--quiet",  # Reduce verbose output
    ] + session_args

    command = base_command + args
    print(f"[Instagram] Executing: {' '.join(command)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Add timeout to prevent hanging
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
        except asyncio.TimeoutError:
            process.kill()
            print(f"[Instagram] Command timed out after 120 seconds")
            return None

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            print(f"[Instagram] Command failed with code {process.returncode}")
            print(f"[Instagram] Error: {error_msg}")
            
            # Check for specific error types
            if "Invalid username" in error_msg:
                print(f"[Instagram] Invalid username/target format")
            elif "Login required" in error_msg or "login" in error_msg.lower():
                print(f"[Instagram] Login/authentication required")
            elif "not found" in error_msg.lower():
                print(f"[Instagram] Content not found")

        if os.path.exists(target_dir):
            # Remove any unwanted profile pictures
            for file in os.listdir(target_dir):
                if "profile_pic" in file:
                    os.remove(os.path.join(target_dir, file))
            
            files = os.listdir(target_dir)
            if files:
                print(f"[Instagram] Successfully downloaded {len(files)} file(s)")
                return target_dir
            else:
                print(f"[Instagram] No files downloaded")
        else:
            print(f"[Instagram] Target directory not created")
            
        return None
    except Exception as e:
        print(f"[Instagram] Exception: {e}")
        return None

# --- Core Functions ---

async def download_insta_post(url: str) -> Optional[str]:
    target_dir = generate_target_dir("insta_post")
    try:
        shortcode = url.split("/p/")[1].split("/")[0]
        return await _run_instaloader(["--", f"-{shortcode}"], target_dir)
    except: return None

async def download_insta_reel(url: str) -> Optional[str]:
    target_dir = generate_target_dir("insta_reel")
    try:
        segment = "/reel/" if "/reel/" in url else "/reels/"
        shortcode = url.split(segment)[1].split("/")[0]
        return await _run_instaloader(["--", f"-{shortcode}"], target_dir)
    except: return None

async def download_insta_story(username: str) -> Optional[str]:
    """Download stories for a username"""
    target_dir = generate_target_dir(f"story_{username}")
    # Use -- before the stories target
    return await _run_instaloader(["--", f":stories-{username}"], target_dir)

async def download_insta_highlight(username: str, highlight_id: Optional[int] = None) -> Optional[str]:
    """
    Download highlights for a username.
    
    Args:
        username: Instagram username
        highlight_id: Specific highlight index (int), None for all highlights
    
    Returns:
        Path to downloaded content or None
    """
    target_dir = generate_target_dir(f"highlight_{username}")
    
    if highlight_id is not None:
        # Download specific highlight using the unique_id
        # Syntax: -- :hl-<highlight_id>
        return await _run_instaloader(["--", f":hl-{highlight_id}"], target_dir)
    else:
        # Download all highlights for the user
        return await _run_instaloader(["--highlights", "--", username], target_dir)

# --- Metadata Functions ---

async def search_instagram_profile(username: str) -> Optional[Dict]:
    try:
        # Retry logic for network issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
                return {
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
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[Instagram] Retry {attempt + 1}/{max_retries} for profile search")
                    await asyncio.sleep(2)  # Wait before retry
                    continue
                else:
                    raise e
    except Exception as e:
        print(f"[Instagram] Profile search failed: {e}")
        return None

async def get_profile_highlights(username: str) -> Optional[List[Dict]]:
    """
    Get list of highlights for a profile.
    
    Returns:
        List of highlight dicts, empty list if none found, None if profile is private/error
    """
    try:
        # Retry logic for network issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
                
                # Check if profile is private and we don't have access
                if profile.is_private:
                    print(f"[Instagram] Profile @{username} is private")
                    return None
                    
                highlights = []
                # get_highlights() is a generator, must be consumed in thread
                hls = await asyncio.to_thread(list, L.get_highlights(profile))
                
                for idx, hl in enumerate(hls):
                    highlights.append({
                        'index': hl.unique_id,  # Use unique_id directly (it's already an int)
                        'title': hl.title,
                        'item_count': hl.itemcount
                    })
                
                return highlights
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[Instagram] Retry {attempt + 1}/{max_retries} for highlights fetch")
                    await asyncio.sleep(2)  # Wait before retry
                    continue
                else:
                    raise e
                    
    except instaloader.exceptions.LoginRequiredException:
        print(f"[Instagram] Login required to view @{username} highlights")
        return None
    except Exception as e:
        print(f"[Instagram] Highlights fetch failed: {e}")
        return []