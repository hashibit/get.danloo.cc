from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta, timezone
import os
import logging

logger = logging.getLogger(__name__)

# JWT configuration
SECRET_KEY = os.environ.get("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


def create_access_token(data: dict, expires_minutes: int = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_minutes is None:
        expires_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def authenticate_ak_sk(request: Request):
    """
    Authenticate using AK/SK from headers.
    Expected headers:
    - X-Access-Key: The access key
    - X-Secret-Key: The secret key
    """
    from services.secret_service import SecretService
    from database import get_database

    access_key = request.headers.get("X-Access-Key")
    secret_key = request.headers.get("X-Secret-Key")

    if not access_key or not secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Access-Key or X-Secret-Key headers",
            headers={"WWW-Authenticate": "AK-SK"},
        )

    try:
        # Get database session
        db = next(get_database())
        secret_service = SecretService()

        # Validate AK/SK pair
        is_valid = secret_service.validate_ak_sk_pair(db, access_key, secret_key)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access key or secret key",
                headers={"WWW-Authenticate": "AK-SK"},
            )

        # Get user by access key
        user = secret_service.get_user_by_access_key(db, access_key)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for access key",
                headers={"WWW-Authenticate": "AK-SK"},
            )

        logger.info(f"AK/SK authentication successful for user {user.id}")
        return {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "auth_type": "ak_sk",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AK/SK authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )
    finally:
        if "db" in locals():
            db.close()


def get_current_user_flexible(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """
    Flexible authentication that supports both JWT and AK/SK.
    First tries JWT Bearer token, then falls back to AK/SK headers.
    """
    # Try JWT authentication first
    if credentials:
        try:
            return get_current_user(credentials)
        except HTTPException:
            pass  # Fall through to AK/SK authentication

    # Try AK/SK authentication
    return authenticate_ak_sk(request)


def get_current_user_optional(
    request: Request,
):
    """
    Optional authentication - returns user info if authenticated, None if not.
    Used for endpoints that work both with and without authentication.
    """
    try:
        # Try JWT authentication first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            if payload:
                return payload

        # Try AK/SK authentication
        access_key = request.headers.get("X-Access-Key")
        secret_key = request.headers.get("X-Secret-Key")
        if access_key and secret_key:
            return authenticate_ak_sk(request)

        return None
    except Exception:
        # If any authentication fails, return None (anonymous user)
        return None


def require_admin(current_user: dict = Depends(get_current_user_flexible)):
    """
    Require admin role for the current user.
    Raises HTTPException if user is not an admin.
    """
    # Check if user has admin role
    # You can customize this based on your user model
    # For now, checking if 'is_admin' or 'role' field exists
    is_admin = current_user.get("is_admin", False) or current_user.get("role") == "admin"

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user
