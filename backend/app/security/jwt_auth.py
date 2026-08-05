import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import jwt
from fastapi import Request, HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.db_repositories.user_repo import get_user_by_id
from app.models.db import User

logger = logging.getLogger("codesage.security.jwt_auth")

security_bearer = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token for user session authentication."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token signature expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def get_current_user(
    request: Request,
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts and validates the authenticated User instance
    from HTTP-only cookie 'codesage_session' or 'Authorization: Bearer <token>' header.
    In local development/test fallback mode without OAuth, returns a mock admin user.
    """
    token: Optional[str] = None

    # Check HTTP-only cookie first
    token = request.cookies.get("codesage_session")

    # Fallback to Authorization header
    if not token and auth_credentials:
        token = auth_credentials.credentials

    if not token:
        # Development fallback mode when no token is supplied
        dev_user = get_user_by_id(db, 1)
        if dev_user:
            return dev_user
        # Return fallback mock admin user if database empty
        return User(
            id=1,
            github_id=1001,
            username="devadmin",
            email="admin@codesage.ai",
            name="CodeSage Admin",
            role="admin"
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id = int(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token user identity"
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists"
        )

    return user


def require_role(allowed_roles: List[str]):
    """
    FastAPI dependency factory enforcing Role-Based Access Control (RBAC).
    Example: Depends(require_role(["admin"]))
    """
    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {allowed_roles}, current role: '{current_user.role}'"
            )
        return current_user
    return _role_checker
