"""
Authentication and Security Utilities

Handles JWT token creation, password hashing, and user authentication for CMP.
"""

import datetime as dt
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select

from .config import settings
from .models import User, UserRole
from .logging_config import get_logger

logger = get_logger("auth")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class AuthorizationError(Exception):
    """Raised when user lacks required permissions"""
    pass


def get_secret_key() -> str:
    """Get JWT secret key from settings"""
    secret = settings.jwt_secret_key or "your-super-secret-jwt-key-change-in-production"
    if secret == "your-super-secret-jwt-key-change-in-production":
        logger.warning("Using default JWT secret key - change this in production!")
    return secret


def hash_password(password: str) -> str:
    """Hash a plain password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[dt.timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = dt.datetime.utcnow() + expires_delta
    else:
        expire = dt.datetime.utcnow() + dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            raise AuthenticationError(f"Invalid token type. Expected {token_type}")
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise AuthenticationError("Token missing expiration")
        
        if dt.datetime.utcnow() > dt.datetime.fromtimestamp(exp):
            raise AuthenticationError("Token has expired")
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise AuthenticationError(f"Invalid token: {e}")


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password"""
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        
        if not user:
            logger.info(f"Authentication failed: user {email} not found")
            return None
        
        if not user.is_active:
            logger.info(f"Authentication failed: user {email} is inactive")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.info(f"Authentication failed: invalid password for {email}")
            return None
        
        # Update last login
        user.last_login = dt.datetime.now(dt.timezone.utc)
        db.commit()
        
        logger.info(f"User {email} authenticated successfully")
        return user
        
    except Exception as e:
        logger.error(f"Authentication error for {email}: {e}")
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def create_user(db: Session, email: str, password: str, full_name: str, role: UserRole = UserRole.VIEWER) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")
    
    # Create new user
    hashed_password = hash_password(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Created user {email} with role {role.value}")
    return user


def require_permission(user: User, required_role: UserRole) -> None:
    """Check if user has required permission, raise exception if not"""
    if not user.has_permission(required_role):
        raise AuthorizationError(f"User {user.email} lacks required permission: {required_role.value}")


def get_current_user_from_token(db: Session, token: str) -> User:
    """Get current user from JWT token"""
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Token missing user ID")
        
        user = get_user_by_id(db, int(user_id))
        if user is None:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User is inactive")
        
        return user
        
    except ValueError:
        raise AuthenticationError("Invalid user ID in token")


def create_token_response(user: User) -> Dict[str, Any]:
    """Create token response for successful authentication"""
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    }
