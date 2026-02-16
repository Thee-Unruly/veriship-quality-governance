"""Authentication routes for user login and registration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import User
from pydantic import BaseModel
from datetime import datetime
import bcrypt
from typing import Optional
try:
    import jwt
except ImportError:
    from jwt import PyJWT as jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Secret key for JWT (in production, use environment variable)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request schema."""
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response with token."""
    token: str
    user: UserResponse


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode(), hash.encode())


def create_token(user_id: int) -> str:
    """Create JWT token."""
    payload = {"sub": str(user_id)}
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        # PyJWT 2.0+ returns string directly
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token creation failed: {str(e)}"
        )


def get_current_user(token: str = None, db: Session = Depends(get_db)) -> User:
    """Get current user from token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/register", response_model=LoginResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(User.username == request.username, User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Construct full name
    name = request.username
    if request.first_name and request.last_name:
        name = f"{request.first_name} {request.last_name}"
    elif request.first_name:
        name = request.first_name

    # Create new user
    user = User(
        username=request.username,
        email=request.email,
        name=name,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role="member",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_token(user.id)
    
    return LoginResponse(
        token=token,
        user=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return token."""
    # Find user by username or email
    user = db.query(User).filter(
        or_(User.username == request.username, User.email == request.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_token(user.id)
    
    return LoginResponse(
        token=token,
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
def get_profile(token: str = None, db: Session = Depends(get_db)):
    """Get current user profile."""
    user = get_current_user(token, db)
    return UserResponse.from_orm(user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    user = get_current_user(token, db)
    
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)
