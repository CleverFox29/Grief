"""Authentication API routes for CGAS (F1, F2, F3)."""

from datetime import timedelta
from fastapi import APIRouter, Depends, status

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    RequestOTPRequest,
    RequestOTPResponse,
    ResetPasswordWithOTPRequest,
    ChangePasswordRequest,
    MessageResponse
)
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.core.deps import get_current_user
from app.models import User
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db = Depends(get_db)):
    """
    Authenticate user with role selection (Student vs Admin) and ID/password (F1, F2).
    Enforces account lockout on 5 failed attempts.
    """
    user = AuthService.authenticate_user(
        db=db,
        role=request.role,
        user_id=request.user_id,
        password=request.password
    )

    # 15-minute inactivity session token (NFR 4.2)
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.user_id, "role": user.role, "name": user.name},
        expires_delta=expires
    )

    user_resp = UserResponse(
        id=user.id,
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        enrollment_no=getattr(user, "enrollment_no", None),
        hostel_room=getattr(user, "hostel_room", None),
        department=getattr(user, "department", None),
        admin_level=getattr(user, "admin_level", None),
        category=getattr(user, "category", None)
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_resp
    )

@router.get("/me", response_model=UserResponse)
def get_current_authenticated_user(current_user: User = Depends(get_current_user)):
    """Return profile details of currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        enrollment_no=getattr(current_user, "enrollment_no", None),
        hostel_room=getattr(current_user, "hostel_room", None),
        department=getattr(current_user, "department", None),
        admin_level=getattr(current_user, "admin_level", None),
        category=getattr(current_user, "category", None)
    )

@router.post("/request-otp", response_model=RequestOTPResponse)
def request_password_reset_otp(request: RequestOTPRequest, db = Depends(get_db)):
    """
    Request a 5-minute single-use OTP for password recovery (F3, U2).
    """
    otp, email = AuthService.request_password_reset_otp(db=db, user_id=request.user_id)
    return RequestOTPResponse(
        message=f"OTP successfully generated and dispatched to registered address ({email}). Valid for {settings.OTP_VALIDITY_MINUTES} minutes.",
        user_id=request.user_id,
        expires_in_minutes=settings.OTP_VALIDITY_MINUTES,
        otp_preview=otp.otp_code  # Provided for lab testing and simulation
    )

@router.post("/reset-password", response_model=MessageResponse)
def reset_password_with_otp(request: ResetPasswordWithOTPRequest, db = Depends(get_db)):
    """
    Verify single-use OTP and reset user password (F3, U2).
    """
    AuthService.reset_password_with_otp(
        db=db,
        user_id=request.user_id,
        otp_code=request.otp_code,
        new_password=request.new_password
    )
    return MessageResponse(
        message="Password successfully updated. You may now log in with your new credentials."
    )

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Change password from an active authenticated session.
    """
    AuthService.change_password(
        db=db,
        user=current_user,
        old_password=request.old_password,
        new_password=request.new_password
    )
    return MessageResponse(
        message="Password successfully changed."
    )
