import os
from .base import FileStorageProvider
from typing import Optional

class LocalStorageProvider(FileStorageProvider):
    def __init__(self, base_path: str = "static", base_url: str = "/static"):
        self.base_path = base_path
        self.base_url = base_url
        os.makedirs(self.base_path, exist_ok=True)
        print("Initialized Local Storage Provider.")

    def upload_file(self, file_bytes: bytes, destination_blob_name: str, content_type: str) -> str:
        full_path = os.path.join(self.base_path, destination_blob_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        return f"{self.base_url}/{destination_blob_name}"

    def download_file_as_bytes(self, blob_name: str) -> Optional[bytes]:
        full_path = os.path.join(self.base_path, blob_name)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return f.read()
        return None

    def delete_file(self, blob_name: str) -> None:
        full_path = os.path.join(self.base_path, blob_name)
        if os.path.exists(full_path):
            os.remove(full_path)
