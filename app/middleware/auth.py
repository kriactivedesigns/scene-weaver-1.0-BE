"""
Authentication middleware for automatic token validation on protected routes.
This middleware intercepts requests and validates JWT tokens before reaching endpoints.
"""

import re
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..services.security import verify_token
from ..api.v1.crud import user as user_crud
from .. import models


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically validate JWT tokens for protected routes.
    
    Public routes (no authentication required):
    - /auth/login
    - /auth/signup
    - /auth/refresh
    - /docs, /redoc, /openapi.json (API documentation)
    - /health, / (health checks)
    
    All other routes require valid JWT tokens.
    """
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = [
        r"^/api/v1/auth/(login|signup|refresh)$",
        r"^/(docs|redoc|openapi\.json).*$",
        r"^/(health|)/?$",
        r"^/favicon\.ico$"
    ]
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate authentication for protected routes.
        """
        path = request.url.path
        method = request.method
        
        # Skip authentication for public routes
        if self._is_public_route(path):
            response = await call_next(request)
            return response
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # Extract and validate token for protected routes
        try:
            user = await self._authenticate_request(request)
            # Add user to request state for use in endpoints
            request.state.current_user = user
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers or {}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    def _is_public_route(self, path: str) -> bool:
        """Check if the route is public (doesn't require authentication)."""
        for pattern in self.PUBLIC_ROUTES:
            if re.match(pattern, path):
                return True
        return False
    
    async def _authenticate_request(self, request: Request) -> models.User:
        """Extract token from request and validate it."""
        # Get Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token from "Bearer <token>" format
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
        token_data = verify_token(token, credentials_exception)
        
        # Get user from database
        db = SessionLocal()
        try:
            user = user_crud.get_user_by_email(db, email=token_data.email)
            if user is None:
                raise credentials_exception
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            return user
        finally:
            db.close()


def get_current_user_from_request(request: Request) -> models.User:
    """
    Helper function to get current user from request state.
    Use this in endpoints that need the current user.
    """
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.current_user