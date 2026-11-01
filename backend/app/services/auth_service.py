"""Authentication service implementing business logic for F1, F2, and F3."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.models import User, Student, Admin, PasswordResetOTP, AuditLog, AuditAction, UserRole
from app.core.security import hash_password, verify_password, generate_otp, create_access_token
from app.config import settings

class AuthService:
    """Service handling user authentication, account security, and OTP password recovery."""

    @staticmethod
    def authenticate_user(db, role: UserRole, user_id: str, password: str) -> User:
        """
        Authenticate user credentials according to F1 and F2.
        - F1: Validates role selection (Student vs Admin) and credentials.
        - F2: Tracks failed password attempts; locks account for 15 minutes after 5 failures.
        """
        user = User.objects(user_id=user_id).first()
        
        # If user does not exist
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not recognized. Please check your credentials or contact administrator."
            )

        # Validate role matches
        if user.role != role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User is registered as '{user.role}', but logged in as '{role.value}'."
            )

        # Check account lock status (F2)
        if user.is_locked():
            lock_time = user.locked_until
            if lock_time.tzinfo is None:
                lock_time = lock_time.replace(tzinfo=timezone.utc)
            remaining_seconds = int((lock_time - datetime.now(timezone.utc)).total_seconds())
            remaining_minutes = max(1, (remaining_seconds + 59) // 60)
            
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked due to 5 failed login attempts. Please try again in {remaining_minutes} minute(s)."
            )

        # Check account active status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact campus administration."
            )

        # Verify password
        if not user.verify_password(password):
            was_locked = user.record_failed_attempt()
            
            if was_locked:
                audit = AuditLog(
                    user_id=user.id,
                    action=AuditAction.ACCOUNT_LOCKED.value,
                    entity_type="USER",
                    entity_id=user.user_id,
                    details=f"Account locked for {settings.ACCOUNT_LOCKOUT_MINUTES} minutes after 5 failed password attempts."
                )
                audit.save()
                user.save()
                
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Invalid password. 5 failed attempts reached. Account is now locked for {settings.ACCOUNT_LOCKOUT_MINUTES} minutes."
                )
            else:
                user.save()
                remaining = settings.MAX_FAILED_LOGIN_ATTEMPTS - user.failed_login_attempts
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid password. {remaining} attempt(s) remaining before your account is locked."
                )

        # Authentication successful: reset counters and log success
        user.reset_failed_attempts()
        user.save()

        audit = AuditLog(
            user_id=user.id,
            action=AuditAction.USER_LOGIN.value,
            entity_type="USER",
            entity_id=user.user_id,
            details=f"Successful login as {user.role}."
        )
        audit.save()
        return user

    @staticmethod
    def request_password_reset_otp(db, user_id: str) -> Tuple[PasswordResetOTP, str]:
        """
        Generate a 5-minute single-use OTP for password recovery (F3, NFR 4.2).
        """
        user = User.objects(user_id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' was not found."
            )

        # Invalidate any existing unused OTPs for this user
        existing_otps = PasswordResetOTP.objects(
            user_id=user.id,
            is_used=False
        )
        for otp in existing_otps:
            otp.mark_used()

        # Generate new 6-digit OTP
        code = generate_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_VALIDITY_MINUTES)
        
        new_otp = PasswordResetOTP(
            user_id=user.id,
            otp_code=code,
            expires_at=expires_at,
            is_used=False
        )
        new_otp.save()

        audit = AuditLog(
            user_id=user.id,
            action=AuditAction.PASSWORD_RESET_OTP.value,
            entity_type="USER",
            entity_id=user.user_id,
            details=f"Password reset OTP generated. Valid for {settings.OTP_VALIDITY_MINUTES} minutes."
        )
        audit.save()

        # In production this dispatches to Email / SMS gateway.
        # For academic lab and dev usage, we return the code for UI simulation.
        return new_otp, user.email

    @staticmethod
    def reset_password_with_otp(db, user_id: str, otp_code: str, new_password: str) -> User:
        """
        Verify single-use OTP and update user password (F3, U2).
        """
        user = User.objects(user_id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        # Fetch latest OTP issued for this user
        otp = PasswordResetOTP.objects(
            user_id=user.id
        ).order_by("-id").first()

        if not otp or not otp.is_valid(otp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP. OTPs are valid for 5 minutes and can only be used once."
            )

        # Set new hashed password and mark OTP used
        user.set_password(new_password)
        otp.mark_used()
        user.reset_failed_attempts()
        user.save()

        audit = AuditLog(
            user_id=user.id,
            action=AuditAction.PASSWORD_CHANGED.value,
            entity_type="USER",
            entity_id=user.user_id,
            details="Password successfully changed via verified OTP."
        )
        audit.save()
        return user

    @staticmethod
    def change_password(db, user: User, old_password: str, new_password: str) -> User:
        """
        Change password for an authenticated session after verifying the current password.
        """
        if not user.verify_password(old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect."
            )

        user.set_password(new_password)
        user.save()

        audit = AuditLog(
            user_id=user.id,
            action=AuditAction.PASSWORD_CHANGED.value,
            entity_type="USER",
            entity_id=user.user_id,
            details="Password changed from authenticated session."
        )
        audit.save()
        return user
