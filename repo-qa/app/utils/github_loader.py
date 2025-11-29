import os
import requests
import shutil
from urllib.parse import urlparse
from app.utils.config import GITHUB_TOKEN

def download_repo(repo_url: str, save_dir="repo"):
    """Downloads and extracts a GitHub repository."""
    parts = urlparse(repo_url)
    user_repo = parts.path.strip("/")
    api_url = f"https://api.github.com/repos/{user_repo}/zipball"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    print(f"[INFO] Downloading repository from {api_url}...")
    r = requests.get(api_url, headers=headers)
    r.raise_for_status() # Ensure the download was successful
    
    os.makedirs(save_dir, exist_ok=True)
    zip_path = os.path.join(save_dir, "repo.zip")
    
    with open(zip_path, "wb") as f:
        f.write(r.content)
    
    # Clean up old extracted dirs before unpacking
    for item in os.listdir(save_dir):
        if item != "repo.zip":
            item_path = os.path.join(save_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)

    shutil.unpack_archive(zip_path, save_dir)
    print(f"[INFO] Repository unpacked in '{save_dir}'.")
    
    # The unpacked folder has a generated name, find it and return its path
    unpacked_dirs = [d for d in os.listdir(save_dir) if os.path.isdir(os.path.join(save_dir, d))]
    if not unpacked_dirs:
        raise Exception("Failed to find the unpacked repository directory.")
        
    return os.path.join(save_dir, unpacked_dirs[0])