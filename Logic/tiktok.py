import os
import yt_dlp
import uuid
import requests
from Token import Tiktok_cookies

def download_tiktok(url, verbose=False): 

    try:
        base_dir = os.path.abspath('downloads') #Root directory
        request_id = str(uuid.uuid4())[:8] # create a uniqe folder so it wont be any problems with many users 
        target_dir = os.path.join(base_dir, f'tk_{request_id}')
        os.makedirs(target_dir, exist_ok=True)

        # Use TikWM API to detect content type and extract info (i used it just to download images from tiktok)
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={
            'url': url,
            'count': 12,
            'cursor': 0,
            'web': 1,
            'hd': 1
        }, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=30)
        
        if response.status_code != 200:
            if verbose:
                print(f"❌ API request failed with status code: {response.status_code}")
            return None
        
        data = response.json()
        
        if data.get('code') != 0:
            if verbose:
                print(f"❌ API Error: {data.get('msg', 'Unknown error')}")
            return None
        
        post_data = data['data']
        author = post_data['author']['unique_id']
        title = post_data.get('title', 'post')[:50]
        
        # Check if it's a photo carousel or video
        if 'images' in post_data and post_data['images']:
            # Photo carousel - download all images
            image_urls = post_data['images']
            
            downloaded_files = [] # save the downloaded files for later
            for idx, img_url in enumerate(image_urls, 1):
                try:
                    
                    img_response = requests.get(img_url, stream=True, timeout=30)
                    if img_response.status_code == 200:
                        filename = f"media_{idx:03d}.jpg"
                        filepath = os.path.join(target_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        downloaded_files.append(filepath)
                except Exception as e:
                    if verbose:
                        print(f"  ⚠️  Failed to download image {idx}: {e}")
            
            if downloaded_files:
                result = {
                    'type': 'carousel',
                    'author': author,
                    'title': title,
                    'likes': post_data.get('digg_count', 0),
                    'comments': post_data.get('comment_count', 0),
                    'shares': post_data.get('share_count', 0),
                    'file_count': len(downloaded_files),
                    'files': downloaded_files,
                    'path': target_dir
                }
                
                if verbose:
                    print(f"✅ Downloaded {len(downloaded_files)} images to: {target_dir}")
                
                return result
            else:
                if verbose:
                    print("❌ No images were downloaded successfully")
                return None
        
        else:
            # Video - use yt-dlp with cookies for better quality
            ydl_opts = {
                'cookiefile': Tiktok_cookies, 
                'outtmpl': os.path.join(target_dir, 'media_%(autonumber)03d.%(ext)s'), 
                'quiet': True,
                'no_warnings': True,
                'format': 'bestvideo+bestaudio/best',
                'writethumbnail': True, 
                'noplaylist': False,
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    valid_exts = ('.mp4', '.mov', '.jpg', '.jpeg', '.png', '.webp', '.heic')
                    files = [f for f in os.listdir(target_dir) if f.lower().endswith(valid_exts)]
                    
                    if not files:
                        if verbose:
                            print("❌ No video files downloaded")
                        return None
                    
                    # Return path string for videos (backward compatibility)
                    if len(files) > 1:
                        return target_dir
                    return os.path.join(target_dir, files[0])
                    
                except Exception as e:
                    if verbose:
                        print(f"❌ TikTok Error: {e}")
                    return None
    
    except Exception as e:
        if verbose:
            print(f"❌ Error: {str(e)}")
        return None