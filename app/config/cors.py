"""
CORS configuration for the SceneWeaver API.
Centralized CORS settings that can be configured via environment variables.
"""

import os
from typing import List

# CORS configuration from environment variables
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
CORS_METHODS = os.getenv("CORS_METHODS", "").split(",")
CORS_HEADERS = os.getenv("CORS_HEADERS", "").split(",")

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