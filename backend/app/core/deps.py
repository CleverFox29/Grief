"""FastAPI dependencies for authentication and role-based access control (RBAC)."""

from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.core.security import decode_access_token
from app.models import User, Student, Admin, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
) -> User:
    """
    Validate Bearer JWT token and return the currently authenticated user.
    Enforces 15-minute inactivity session timeout (NFR 4.2).
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User.objects(user_id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    return user

def require_role(allowed_roles: List[UserRole]) -> Callable[[User], User]:
    """Factory creating dependency enforcing specific user roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed_values = [r.value for r in allowed_roles]
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This endpoint requires one of {[r.value for r in allowed_roles]} role(s).",
            )
        return current_user
    return role_checker

# Shortcuts
require_student = require_role([UserRole.STUDENT])
require_admin = require_role([UserRole.ADMIN])
require_serviceman = require_role([UserRole.SERVICEMAN])
require_serviceman_or_admin = require_role([UserRole.SERVICEMAN, UserRole.ADMIN])
require_student_or_admin = require_role([UserRole.STUDENT, UserRole.ADMIN])
