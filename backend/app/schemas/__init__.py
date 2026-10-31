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
    StaffResponse,
    DuplicateCheckRequest,
    DuplicateMatch,
    DuplicateCheckResponse,
    TicketResponse,
    TicketLogResponse,
    TicketItemResponse,
    TicketDetailResponse,
    UpdateTicketRequest,
    NotificationResponse
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
    "StaffResponse",
    "DuplicateCheckRequest",
    "DuplicateMatch",
    "DuplicateCheckResponse",
    "TicketLogResponse",
    "TicketItemResponse",
    "TicketDetailResponse",
    "UpdateTicketRequest",
    "NotificationResponse"
]
