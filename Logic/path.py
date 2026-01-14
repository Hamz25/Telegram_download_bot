#in here will create a file 
import uuid 
import os 

def generate_target_dir(platform_name):
    base_dir = os.path.abspath('downloads') #Root directory
    request_id = str(uuid.uuid4())[:8] # create a uniqe folder so it wont be any problems with many users 
    target_dir = os.path.join(base_dir, f'{platform_name}_{request_id}')
    return target_dir