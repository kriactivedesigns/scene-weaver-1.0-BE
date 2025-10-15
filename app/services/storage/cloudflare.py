import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from .base import FileStorageProvider
from typing import Optional

class CloudflareStorageProvider(FileStorageProvider):
    """
    Cloudflare R2 storage provider using S3-compatible API.
    R2 offers zero egress fees and S3-compatible API.
    """
    
    def __init__(self, bucket_name: str, account_id: str = None, access_key_id: str = None, secret_access_key: str = None):
        self.bucket_name = bucket_name
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        
        # Cloudflare R2 credentials
        access_key = access_key_id or os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        secret_key = secret_access_key or os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        
        if not all([self.account_id, access_key, secret_key]):
            raise ValueError(
                "Cloudflare R2 requires CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_R2_ACCESS_KEY_ID, "
                "and CLOUDFLARE_R2_SECRET_ACCESS_KEY environment variables"
            )
        
        # Cloudflare R2 endpoint URL
        endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        # Configure boto3 client for Cloudflare R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                region_name='auto',  # R2 uses 'auto' as region
                signature_version='v4',
                s3={
                    'addressing_style': 'path'  # Use path-style addressing
                }
            )
        )
        
        # Set up public URL for accessing files
        self.public_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL")
        
        # Remove trailing slash if present
        self.public_url = self.public_url.rstrip('/')
        
        print(f"Initialized Cloudflare R2 Storage Provider for bucket: {self.bucket_name}")
        
        # Test bucket access on initialization
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """
        Ensure the bucket exists, create if it doesn't.
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"Created bucket: {self.bucket_name}")
                except ClientError as create_error:
                    print(f"Failed to create bucket {self.bucket_name}: {create_error}")
                    raise
            else:
                print(f"Error accessing bucket {self.bucket_name}: {e}")
                raise
    
    def upload_file(self, file_bytes: bytes, destination_blob_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Uploads file bytes to Cloudflare R2.
        
        Args:
            file_bytes: The raw bytes of the file to upload
            destination_blob_name: The full path for the object (e.g., 'characters/uuid.png')
            content_type: The MIME type of the file
            
        Returns:
            The publicly accessible URL of the uploaded file
        """
        try:
            # Extra metadata for better file handling
            extra_args = {
                'ContentType': content_type,
                'CacheControl': 'public, max-age=3600',  # Cache for 1 hour
            }
            
            # Only apply gzip compression to text-based files
            if not content_type.startswith('image/') and not content_type.startswith('video/'):
                extra_args['ContentEncoding'] = 'gzip'
                extra_args['Metadata'] = {
                    'compressed': 'gzip',
                    'original-content-type': content_type
                }
            else:
                extra_args['Metadata'] = {
                    'type': content_type.split('/')[0],  # 'image' or 'video'
                    'optimized': 'true'
                }
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination_blob_name,
                Body=file_bytes,
                **extra_args
            )
            
            # Return public URL
            return f"{self.public_url}/{destination_blob_name}"
            
        except ClientError as e:
            print(f"Failed to upload file to R2: {e}")
            raise Exception(f"R2 upload failed: {str(e)}")
    
    def download_file_as_bytes(self, blob_name: str) -> Optional[bytes]:
        """
        Downloads a file from Cloudflare R2 and returns its content as bytes.
        
        Args:
            blob_name: The full path of the object to download, or a full URL
            
        Returns:
            The file content as bytes, or None if the file is not found
        """
        try:
            # Handle both blob names and full URLs
            if blob_name.startswith('http'):
                # Extract blob name from URL
                # Example: https://pub-bee2b9eafa9645a1b6d5107545fd2357.r2.dev/characters/uuid.png
                # Should become: characters/uuid.png
                if self.public_url in blob_name:
                    blob_name = blob_name.replace(self.public_url + '/', '')
                else:
                    # Fallback: extract everything after the domain
                    from urllib.parse import urlparse
                    parsed_url = urlparse(blob_name)
                    blob_name = parsed_url.path.lstrip('/')
            
            print(f"Attempting to download R2 file: {blob_name}")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=blob_name
            )
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"File not found in R2: {blob_name}")
                return None
            else:
                print(f"Error downloading file from R2: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error downloading from R2: {e}")
            return None
    
    def delete_file(self, blob_name: str) -> None:
        """
        Deletes a file from Cloudflare R2.
        
        Args:
            blob_name: The full path of the object to delete
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=blob_name
            )
            print(f"Successfully deleted file from R2: {blob_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"Notice: File {blob_name} not found in R2 (may already be deleted)")
            else:
                print(f"Error deleting file from R2: {e}")
        except Exception as e:
            print(f"Unexpected error deleting from R2: {e}")
    
    def list_files(self, prefix: str = "") -> list:
        """
        List files in the bucket with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
                
        except ClientError as e:
            print(f"Error listing files from R2: {e}")
            return []
    
    def get_file_info(self, blob_name: str) -> Optional[dict]:
        """
        Get metadata information about a file.
        
        Args:
            blob_name: The full path of the object
            
        Returns:
            Dictionary with file metadata or None if not found
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=blob_name
            )
            
            return {
                'size': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                print(f"Error getting file info from R2: {e}")
                return None