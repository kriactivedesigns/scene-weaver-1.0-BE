import os
from dotenv import load_dotenv
from .base import FileStorageProvider
from .gcp import GCPStorageProvider
from .local import LocalStorageProvider
from .cloudflare import CloudflareStorageProvider

# Load environment variables
load_dotenv()

def get_storage_provider() -> FileStorageProvider:
    """
    Factory function to get the configured storage provider instance
    based on the STORAGE_PROVIDER environment variable.
    """
    provider = os.getenv("STORAGE_PROVIDER", "local").lower()
    
    # Add beautiful icons for different storage providers
    provider_icons = {
        "gcp": "☁️",
        "cloudflare-r2": "⚡",
        "local": "🏠"
    }
    
    icon = provider_icons.get(provider, "💾")
    print(f"{icon} Using storage provider: {provider}")
    
    if provider == "gcp":
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("GCP_BUCKET_NAME env var must be set for GCP provider.")
        return GCPStorageProvider(bucket_name=bucket_name)
    
    elif provider == "cloudflare-r2":
        bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("CLOUDFLARE_R2_BUCKET_NAME env var must be set for Cloudflare provider.")
        return CloudflareStorageProvider(bucket_name=bucket_name)
    
    elif provider == "local":
        return LocalStorageProvider()
        
    else:
        raise ValueError(f"Unsupported storage provider: {provider}. Supported: 'local', 'gcp', 'cloudflare-r2'")

# Create a single, shared instance to be imported by the rest of the application
storage_provider = get_storage_provider()

# Get the current provider type for status message
current_provider = os.getenv("STORAGE_PROVIDER", "local").lower()

# Display storage initialization status with beautiful icons
provider_status = {
    "gcp": "☁️ Google Cloud Storage initialized",
    "cloudflare-r2": "⚡ Cloudflare R2 Storage initialized",
    "local": "🏠 Local File Storage initialized"
}

status_message = provider_status.get(current_provider, f"💾 {current_provider.title()} Storage initialized")
print(f"✅ {status_message}")
