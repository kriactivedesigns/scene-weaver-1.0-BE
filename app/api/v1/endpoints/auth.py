from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ....api.dependencies import get_db
from ....services.security import create_tokens, verify_token, refresh_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from .... import schemas, models
from ..crud import user as user_crud

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token, credentials_exception)
    user = user_crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

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

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

@router.get("/users", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    """Get a list of users (requires authentication)."""
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users