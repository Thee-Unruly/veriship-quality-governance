"""Authentication routes for user login and registration."""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import User, ServiceAccount
from pydantic import BaseModel
from datetime import datetime, timezone
import bcrypt
from typing import Optional, List
try:
    import jwt
except ImportError:
    from jwt import PyJWT as jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Secret key for JWT — read from environment, fall back to dev key
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
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


# ========== Service Account Management (for n8n / CI bots) ==========

class ServiceAccountCreate(BaseModel):
    """Payload for creating a service account."""
    name: str              # e.g. "n8n-agent"
    description: Optional[str] = None
    role: str = "agent"   # agent | readonly | admin


class ServiceAccountResponse(BaseModel):
    """Service account info (without the token)."""
    id: int
    name: str
    description: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class ServiceAccountTokenResponse(BaseModel):
    """Service account creation response with token."""
    account: ServiceAccountResponse
    token: str
    token_type: str = "Bearer"
    note: str = (
        "This token does not expire. Store it securely in n8n "
        "as an HTTP Header credential: Authorization: Bearer <token>"
    )


def create_service_account_token(account_id: int, name: str, role: str) -> str:
    """Create a non-expiring JWT for a service account."""
    payload = {
        "sub": f"sa:{account_id}",
        "name": name,
        "role": role,
        "type": "service_account",
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


@router.post("/service-account", response_model=ServiceAccountTokenResponse, status_code=201)
def create_service_account(payload: ServiceAccountCreate, db: Session = Depends(get_db)):
    """
    Provision a new service account for an automated agent (e.g. n8n).

    Returns a **non-expiring Bearer token** that the agent should store as
    an HTTP Header credential in n8n:  
    `Authorization: Bearer <token>`

    Roles:
    - **agent** — read + write on projects, defects, releases, approvals  
    - **readonly** — read-only access  
    - **admin** — full access  
    """
    existing = db.query(ServiceAccount).filter(ServiceAccount.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service account '{payload.name}' already exists. "
                   "Use POST /api/auth/service-account/token to get a new token."
        )

    account = ServiceAccount(
        name=payload.name,
        description=payload.description,
        role=payload.role,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    token = create_service_account_token(account.id, account.name, account.role)

    return ServiceAccountTokenResponse(
        account=ServiceAccountResponse.from_orm(account),
        token=token,
    )


@router.post("/service-account/token", response_model=ServiceAccountTokenResponse)
def reissue_service_account_token(name: str, db: Session = Depends(get_db)):
    """
    Re-issue a Bearer token for an **existing** service account (token rotation).

    Pass the account name as a query param:  
    `POST /api/auth/service-account/token?name=n8n-agent`
    """
    account = db.query(ServiceAccount).filter(
        ServiceAccount.name == name,
        ServiceAccount.is_active == True,
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active service account '{name}' not found."
        )

    token = create_service_account_token(account.id, account.name, account.role)

    return ServiceAccountTokenResponse(
        account=ServiceAccountResponse.from_orm(account),
        token=token,
    )


@router.get("/service-accounts", response_model=List[ServiceAccountResponse])
def list_service_accounts(db: Session = Depends(get_db)):
    """List all service accounts (for admin visibility)."""
    return db.query(ServiceAccount).order_by(ServiceAccount.created_at.desc()).all()


@router.delete("/service-account/{name}", status_code=200)
def deactivate_service_account(name: str, db: Session = Depends(get_db)):
    """
    Deactivate a service account (revokes its token without deleting the record).
    The account's JWT will be rejected on next use once you add middleware checks.
    """
    account = db.query(ServiceAccount).filter(ServiceAccount.name == name).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Service account '{name}' not found.")
    account.is_active = False
    db.commit()
    return {"status": "deactivated", "name": name}
