"""Pydantic validation schemas for API inputs and responses."""

from app.schemas.auth import (
    LoginRequest,
    UserResponse,
    TokenResponse,
    RequestOTPRequest,
    RequestOTPResponse,
    ResetPasswordWithOTPRequest,
    ChangePasswordRequest,
    MessageResponse
)

__all__ = [
    "LoginRequest",
    "UserResponse",
    "TokenResponse",
    "RequestOTPRequest",
    "RequestOTPResponse",
    "ResetPasswordWithOTPRequest",
    "ChangePasswordRequest",
    "MessageResponse"
]
