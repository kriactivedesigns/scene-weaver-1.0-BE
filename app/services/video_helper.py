import os

def get_relative_path(videoPath: str) -> str:
    return videoPath.lstrip('/')

def get_video_path_to_save() -> str:
    """Returns the base directory for saving animatic videos."""
    return 'static/videos'

def save_video_in_db(video_path: str, video_bytes: bytes) -> bool:
    """Saves video bytes to the specified path, creating dirs if needed."""
    try:
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        with open(video_path, "wb") as f:
            f.write(video_bytes)
        return True
    except IOError as e:
        print(f"Error creating video file {video_path}: {e}")
        return False
