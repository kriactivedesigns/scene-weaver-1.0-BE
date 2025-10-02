from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ....api.dependencies import get_db
from ....services.security import create_tokens, refresh_access_token
from .... import schemas, models
from ..crud import user as user_crud
from ....middleware.auth import get_current_user_from_request

router = APIRouter()

@router.post("/signup", response_model=schemas.UserAuthResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return user object with both tokens."""
    # Create the user
    created_user = user_crud.create_user(db=db, user=user)
    
    # Generate both access and refresh tokens
    tokens = create_tokens(created_user.email)
    
    return {
        "user": created_user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }

@router.post("/login", response_model=schemas.UserAuthResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with JSON payload and return user object with both tokens."""
    user = user_crud.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate both access and refresh tokens
    tokens = create_tokens(user.email)
    
    return {
        "user": user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }

@router.post("/refresh", response_model=schemas.TokenRefreshResponse)
def refresh_token(refresh_request: schemas.TokenRefreshRequest):
    """Generate a new access token using a refresh token."""
    new_access_token = refresh_access_token(refresh_request.refresh_token)
    return {
        "access_token": new_access_token
    }

@router.get("/me", response_model=schemas.UserAuth)
def get_current_user_profile(request: Request):
    """Get current user profile information."""
    current_user = get_current_user_from_request(request)
    return current_user