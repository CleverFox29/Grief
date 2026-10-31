"""PasswordResetOTP entity representing one-time verification tokens."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import utc_now

class PasswordResetOTP(Base):
    """
    Temporary OTP issued for password reset (F3, NFR 4.2).
    Valid for 5 minutes and single-use only.
    """
    __tablename__ = "password_reset_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationship
    user = relationship("User")

    def is_valid(self, code: str) -> bool:
        """Check if OTP matches, has not been used, and has not expired."""
        if self.is_used or self.otp_code != code:
            return False
        
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= exp

    def mark_used(self) -> None:
        """Invalidate token after successful verification."""
        self.is_used = True

    def __repr__(self) -> str:
        return f"<PasswordResetOTP user_id={self.user_id} used={self.is_used}>"
