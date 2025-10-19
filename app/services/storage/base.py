from abc import ABC, abstractmethod
from typing import Optional

class FileStorageProvider(ABC):
    """
    An abstract interface for a file storage provider.
    This defines the contract for uploading, downloading, and deleting files,
    ensuring that any provider can be swapped in seamlessly.
    """
    
    @abstractmethod
    def upload_file(self, file_bytes: bytes, destination_blob_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Uploads file bytes to the storage.

        Args:
            file_bytes: The raw bytes of the file to upload.
            destination_blob_name: The full path for the object (e.g., 'characters/uuid.png').
            content_type: The MIME type of the file.

        Returns:
            The publicly accessible URL of the uploaded file.
        """
        pass

    @abstractmethod
    def download_file_as_bytes(self, blob_name: str) -> Optional[bytes]:
        """
        Downloads a file from storage and returns its content as bytes.

        Args:
            blob_name: The full path of the object to download.

        Returns:
            The file content as bytes, or None if the file is not found.
        """
        pass

    @abstractmethod
    def delete_file(self, blob_name: str) -> None:
        """
        Deletes a file from the storage.

        Args:
            blob_name: The full path of the object to delete.
        """
        pass