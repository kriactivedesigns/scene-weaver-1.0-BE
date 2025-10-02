"""
Helper dependencies for accessing middleware-authenticated users in endpoints.
"""

from fastapi import Request, Depends
from ... import models
from ...middleware import get_current_user_from_request


def get_current_user(request: Request) -> models.User:
    """
    Get the current authenticated user from request state (set by AuthenticationMiddleware).
    Use this dependency in endpoints that need the current user.
    
    Example:
        @router.get("/my-projects")
        def get_my_projects(
            current_user: models.User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            return get_projects_by_owner(db, owner_id=current_user.id)
    """
    return get_current_user_from_request(request)


def get_current_active_user(request: Request) -> models.User:
    """
    Get the current authenticated and active user from request state.
    This is an alias for get_current_user since the middleware already checks is_active.
    """
    return get_current_user_from_request(request)