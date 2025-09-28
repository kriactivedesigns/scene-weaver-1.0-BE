from google.cloud import storage
import os
from typing import Optional

BUCKET_NAME = "sceneweaver-static-assets"

try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
except Exception as e:
    print(f"CRITICAL: Failed to initialize Google Cloud Storage client: {e}")
    storage_client = None
    bucket = None

def upload_file_from_bytes(file_bytes: bytes, destination_blob_name: str, content_type: str = 'image/png') -> Optional[str]:
    """
    Uploads file bytes to a GCS bucket and makes it public.
    
    Args:
        file_bytes: The raw bytes of the file to upload.
        destination_blob_name: The full path for the object in the bucket (e.g., 'characters/uuid.png').
        content_type: The MIME type of the file.
        
    Returns:
        The public URL of the uploaded file, or None if the upload fails.
    """
    if not bucket:
        print("GCS bucket is not initialized. Cannot upload file.")
        return None
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
        return blob.public_url
    except Exception as e:
        print(f"Failed to upload to GCS bucket '{BUCKET_NAME}': {e}")
        return None

def delete_file(blob_name: str):
    """Deletes a file from the GCS bucket."""
    if not bucket:
        return
    try:
        blob = bucket.blob(blob_name)
        blob.delete()
        print(f"Successfully deleted {blob_name} from GCS.")
    except Exception as e:
        print(f"Failed to delete {blob_name} from GCS: {e}")

def download_file_as_bytes(blob_name: str) -> bytes | None:
    """Downloads a file from GCS and returns its content as bytes."""
    if not bucket:
        print("GCS bucket is not initialized. Cannot download file.")
        return None
    try:
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    except Exception as e:
        print(f"Failed to download {blob_name} from GCS: {e}")
        return None