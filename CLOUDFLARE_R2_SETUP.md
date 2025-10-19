# Cloudflare R2 Storage Setup Guide

## Overview
Cloudflare R2 is an S3-compatible object storage service that offers:
- Zero egress fees
- S3-compatible API
- Global distribution
- Cost-effective storage pricing

## Setup Instructions

### 1. Create Cloudflare R2 Bucket
1. Log into Cloudflare Dashboard
2. Go to R2 Object Storage
3. Create a new bucket
4. Note the bucket name

### 2. Generate R2 API Tokens
1. Go to R2 → Manage R2 API tokens
2. Create a new API token with:
   - Read permissions for your bucket
   - Write permissions for your bucket
3. Note the Access Key ID and Secret Access Key

### 3. Configure Environment Variables
```bash
# Storage Configuration
STORAGE_PROVIDER="cloudflare"
CLOUDFLARE_ACCOUNT_ID="your-cloudflare-account-id"
CLOUDFLARE_R2_BUCKET_NAME="your-bucket-name"
CLOUDFLARE_R2_ACCESS_KEY_ID="your-access-key-id"
CLOUDFLARE_R2_SECRET_ACCESS_KEY="your-secret-access-key"

# Optional: Custom Domain for Public URLs
CLOUDFLARE_R2_CUSTOM_DOMAIN="files.yourdomain.com"
```

### 4. Public Access Setup (Optional)
To serve files publicly:
1. In R2 bucket settings, enable "Public URL access"
2. Set up custom domain (recommended) or use default R2 public URL
3. Configure CORS if needed for web access

## Features Included

### Core Storage Operations
- ✅ Upload files with proper content types
- ✅ Download files as bytes
- ✅ Delete files
- ✅ Automatic bucket creation
- ✅ Error handling and logging

### Optimization Features
- ✅ Automatic compression for text files (not images/videos)
- ✅ Cache control headers (1 hour cache)
- ✅ Proper metadata for different file types
- ✅ S3-compatible multipart uploads for large files

### Additional Utilities
- ✅ List files with prefix filtering
- ✅ Get file metadata and info
- ✅ Public URL generation
- ✅ Custom domain support

## Usage Example

The storage provider is automatically configured based on environment variables:

```python
from app.services.storage import storage_provider

# Upload a file
public_url = storage_provider.upload_file(
    file_bytes=image_bytes,
    destination_blob_name="characters/uuid.png",
    content_type="image/png"
)

# Download a file
file_bytes = storage_provider.download_file_as_bytes("characters/uuid.png")

# Delete a file
storage_provider.delete_file("characters/uuid.png")
```

## Benefits of Cloudflare R2

1. **Cost Effective**: No egress fees, lower storage costs
2. **Performance**: Global CDN distribution
3. **Compatibility**: S3-compatible API, easy migration
4. **Reliability**: Cloudflare's global infrastructure
5. **Security**: Built-in DDoS protection and security features

## Migration from GCS to R2

Simply change the environment variable:
```bash
# From GCS
STORAGE_PROVIDER="gcp"

# To Cloudflare R2
STORAGE_PROVIDER="cloudflare"
```

All application code remains unchanged due to the abstract storage provider interface!