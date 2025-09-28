import os
from vertexai.preview.vision_models import Image

def get_relative_path(imagePath: str) -> str:
    return imagePath.lstrip('/')

def get_image_path_to_save() -> str:
    return 'static/images'

def load_image(relativePath: str) -> Image:
    return Image.load_from_file(location=relativePath)

def save_image_in_db(image_path: str, image_bytes: bytes) -> bool:
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    try:
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        return True
    except IOError as e:
        print(f"Error creating file {image_path}: {e}")
        return False
