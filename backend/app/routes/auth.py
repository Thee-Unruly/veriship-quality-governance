"""Authentication routes for user login and registration."""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# HTTPBearer scheme — extracts token from "Authorization: Bearer <token>" header
security = HTTPBearer()


# ========== Pydantic Schemas ==========

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


# ========== Password Helpers ==========

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode(), hash.encode())


# ========== Token Helpers ==========

def create_token(user_id: int) -> str:
    """Create JWT token for a regular user."""
    payload = {"sub": str(user_id)}
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token creation failed: {str(e)}"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate the Bearer token from the Authorization header,
    then return the corresponding User from the database.

    Use this as a dependency in any route that should be user-scoped:
        current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials  # pulled from "Authorization: Bearer <token>"

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Service account tokens have "sub" like "sa:123" — reject them here
    if subject.startswith("sa:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service account tokens cannot be used for user endpoints"
        )

    user = db.query(User).filter(User.id == int(subject)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


# ========== Auth Routes ==========

@router.post("/register", response_model=LoginResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
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

    token = create_token(user.id)

    return LoginResponse(token=token, user=UserResponse.from_orm(user))


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return token."""
    user = db.query(User).filter(
        or_(User.username == request.username, User.email == request.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token = create_token(user.id)

    return LoginResponse(token=token, user=UserResponse.from_orm(user))


@router.get("/me", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the currently logged-in user's profile."""
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the currently logged-in user's profile."""
    if first_name is not None:
        current_user.first_name = first_name
    if last_name is not None:
        current_user.last_name = last_name

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return UserResponse.from_orm(current_user)


# ========== Service Account Management ==========

class ServiceAccountCreate(BaseModel):
    name: str
    description: Optional[str] = None
    role: str = "agent"


class ServiceAccountResponse(BaseModel):
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


def get_current_service_account(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> ServiceAccount:
    """
    Validate a service account Bearer token and return the ServiceAccount.
    Use as a dependency in routes meant for automated agents.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str = payload.get("sub", "")
        if not subject.startswith("sa:"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a service account token"
            )
        account_id = int(subject.split(":")[1])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service account token"
        )

    account = db.query(ServiceAccount).filter(
        ServiceAccount.id == account_id,
        ServiceAccount.is_active == True
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service account not found or deactivated"
        )

    # Update last used timestamp
    account.last_used_at = datetime.utcnow()
    db.commit()

    return account


@router.post("/service-account", response_model=ServiceAccountTokenResponse, status_code=201)
def create_service_account(payload: ServiceAccountCreate, db: Session = Depends(get_db)):
    """
    Provision a new service account for an automated agent (e.g. n8n).

    Returns a non-expiring Bearer token. Store it as an HTTP Header credential:
    Authorization: Bearer <token>

    Roles: agent | readonly | admin
    """
    existing = db.query(ServiceAccount).filter(ServiceAccount.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service account '{payload.name}' already exists."
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
    """Re-issue a Bearer token for an existing service account (token rotation)."""
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
    """List all service accounts (admin visibility)."""
    return db.query(ServiceAccount).order_by(ServiceAccount.created_at.desc()).all()


@router.delete("/service-account/{name}", status_code=200)
def deactivate_service_account(name: str, db: Session = Depends(get_db)):
    """Deactivate a service account (revokes its token without deleting the record)."""
    account = db.query(ServiceAccount).filter(ServiceAccount.name == name).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Service account '{name}' not found.")
    account.is_active = False
    db.commit()
    return {"status": "deactivated", "name": name}