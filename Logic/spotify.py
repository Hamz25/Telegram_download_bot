import os
import subprocess
import glob
from Logic.path import generate_target_dir

def download_spotify_track(url):
    download_path = generate_target_dir('spotify')
    if not os.path.exists(download_path): 
        os.makedirs(download_path)

    try:
        # Run spotdl command
        subprocess.run(
            ["spotdl", "download", url, "--output", download_path, "--format", "mp3"],
            check=True,
            capture_output=True
        )
        
        # Find the newest .mp3 in the folder
        list_of_files = glob.glob(f'{download_path}/*.mp3')
        if not list_of_files:
            return None
            
        latest_file = max(list_of_files, key=os.path.getctime)
        filename = os.path.basename(latest_file).replace(".mp3", "")

        # spotDL default naming is "Artist - Song Name"
        # We split by the first " - " to get the artist
        if " - " in filename:
            performer, title = filename.split(" - ", 1)
        else:
            performer = "Unknown Artist"
            title = filename
        
        return {
            "path": latest_file,
            "title": title,
            "performer": performer, # Now returns the actual artist name
            "thumb": None # Metadata is already embedded in the MP3
        }
    except Exception as e:
        print(f"Console Error (spotDL): {e}")
        return None