import os
from .base import FileStorageProvider
from .gcp import GCPStorageProvider
from .local import LocalStorageProvider

def get_storage_provider() -> FileStorageProvider:
    """
    Factory function to get the configured storage provider instance
    based on the STORAGE_PROVIDER environment variable.
    """
    provider = os.getenv("STORAGE_PROVIDER", "local").lower()
    
    if provider == "gcp":
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("GCP_BUCKET_NAME env var must be set for GCP provider.")
        return GCPStorageProvider(bucket_name=bucket_name)
    
    elif provider == "local":
        return LocalStorageProvider()
        
    else:
        raise ValueError(f"Unsupported storage provider: {provider}")

# Create a single, shared instance to be imported by the rest of the application
storage_provider = get_storage_provider()
