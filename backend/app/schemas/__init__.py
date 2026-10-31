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
from app.schemas.ticket import (
    CategoryResponse,
    DuplicateCheckRequest,
    DuplicateMatch,
    DuplicateCheckResponse,
    TicketResponse
)

__all__ = [
    "LoginRequest",
    "UserResponse",
    "TokenResponse",
    "RequestOTPRequest",
    "RequestOTPResponse",
    "ResetPasswordWithOTPRequest",
    "ChangePasswordRequest",
    "MessageResponse",
    "CategoryResponse",
    "DuplicateCheckRequest",
    "DuplicateMatch",
    "DuplicateCheckResponse",
    "TicketResponse"
]
