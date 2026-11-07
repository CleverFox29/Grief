"""Pydantic schemas for authentication and password management."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import UserRole

class LoginRequest(BaseModel):
    user_id: str = Field(..., description="Student Enrollment ID or Admin ID")
    password: str = Field(..., min_length=1, description="Account password")
    role: UserRole = Field(..., description="Role selected on login page: STUDENT or ADMIN")

class UserResponse(BaseModel):
    id: int
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    enrollment_no: Optional[str] = None
    hostel_room: Optional[str] = None
    department: Optional[str] = None
    admin_level: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse

class RequestOTPRequest(BaseModel):
    user_id: str = Field(..., description="User ID for which to request a reset OTP")

class RequestOTPResponse(BaseModel):
    message: str
    user_id: str
    expires_in_minutes: int
    # Note: In development/lab testing, otp_preview helps testers when no real SMS/SMTP is hooked up
    otp_preview: Optional[str] = None

class ResetPasswordWithOTPRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(..., min_length=6, description="New secure password")

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New secure password")

class MessageResponse(BaseModel):
    message: str
    success: bool = True
