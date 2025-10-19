"""
Central dependencies for the API endpoints.
"""
import uuid
from typing import Generator
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..middleware import get_current_user_from_request
from ..services.user_context import UserContextService
from .. import models


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides database session to endpoints
    and ensures it's closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request) -> models.User:
    """
    Dependency that provides the current authenticated user.
    The user is extracted from the request state set by AuthenticationMiddleware.
    """
    return get_current_user_from_request(request)


def get_user_service(
    request: Request, 
    db: Session = Depends(get_db)
) -> UserContextService:
    """
    Dependency that provides UserContextService for the current authenticated user.
    This service handles user-scoped data access and validation.
    """
    current_user = get_current_user_from_request(request)
    return UserContextService(db, current_user.id)