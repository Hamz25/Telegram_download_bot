import subprocess
from Logic.utils.path import generate_target_dir
import os

def Download_snap_short(url):

    try:

        target_dir = generate_target_dir('snapchat') + ".mp4" #create the directory 
        

        os.makedirs(target_dir, exist_ok=True) 

        target = os.path.join(target_dir,"snap_%(autonumber)03d.%(ext)s") #create the folder and put it inside the directory
        command = ['yt-dlp','-o',target, url] # the command that will be used for the subprocess

        result = subprocess.run(command,check=True) # The output
        
        print(f"[Snapchat]: success the targit dir is :{target_dir}")
        
        return target_dir # it will return the path of the directory so it can be deleted later
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e.stderr}")
        return None