"""
CORS configuration for the SceneWeaver API.
Centralized CORS settings that can be configured via environment variables.
"""

import os
from typing import List

# CORS configuration from environment variables
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",") if origin.strip()]

CORS_METHODS_ENV = os.getenv("CORS_METHODS") 
CORS_METHODS = [method.strip() for method in CORS_METHODS_ENV.split(",") if method.strip()]

CORS_HEADERS_ENV = os.getenv("CORS_HEADERS")
CORS_HEADERS = [header.strip() for header in CORS_HEADERS_ENV.split(",") if header.strip()]

CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS")

def get_cors_headers(origin: str = None) -> dict:
    """
    Get CORS headers for responses.
    
    Args:
        origin: The origin from the request. If provided and allowed, will be used.
                If not provided, will use the first allowed origin.
    
    Returns:
        dict: CORS headers to include in responses
    """
    # Use provided origin if it's in allowed origins, otherwise use first allowed origin
    allowed_origin = CORS_ORIGINS[0]  # Default to first origin
    
    if origin and origin in CORS_ORIGINS:
        allowed_origin = origin

    print("CORS Headers:", allowed_origin)
    
    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": str(CORS_CREDENTIALS).lower(),
        "Access-Control-Allow-Methods": ",".join(CORS_METHODS),
        "Access-Control-Allow-Headers": ",".join(CORS_HEADERS)
    }

def is_origin_allowed(origin: str) -> bool:
    """
    Check if an origin is allowed.
    
    Args:
        origin: The origin to check
        
    Returns:
        bool: True if origin is allowed, False otherwise
    """
    return origin in CORS_ORIGINS