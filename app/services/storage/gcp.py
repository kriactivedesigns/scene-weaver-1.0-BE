from google.cloud import storage
from .base import FileStorageProvider
from typing import Optional

class GCPStorageProvider(FileStorageProvider):
    def __init__(self, bucket_name: str):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        print(f"Initialized GCP Storage Provider for bucket: {bucket_name}")

    def upload_file(self, file_bytes: bytes, destination_blob_name: str, content_type: str) -> str:
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
        return f"https://storage.googleapis.com/{self.bucket.name}/{destination_blob_name}"

    def download_file_as_bytes(self, blob_name: str) -> Optional[bytes]:
        blob = self.bucket.blob(blob_name)
        try:
            return blob.download_as_bytes()
        except Exception:
            return None

    def delete_file(self, blob_name: str) -> None:
        blob = self.bucket.blob(blob_name)
        try:
            blob.delete()
        except Exception as e:
            print(f"Notice: Could not delete blob {blob_name}. It may not exist. Error: {e}")
