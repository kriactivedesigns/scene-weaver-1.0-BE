"""
Central dependencies for the API endpoints.
"""
from typing import Generator
from sqlalchemy.orm import Session
from ..database import SessionLocal


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