"""PasswordResetOTP entity representing one-time verification tokens."""

from datetime import datetime, timezone
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, SequenceField
from app.models.base import utc_now

class PasswordResetOTP(Document):
    """
    Temporary OTP issued for password reset (F3, NFR 4.2).
    Valid for 5 minutes and single-use only.
    """
    meta = {
        "collection": "password_reset_otps",
        "indexes": [
            "user_id",
            "otp_code",
            "is_used"
        ]
    }

    id = SequenceField(primary_key=True)
    user_id = IntField(required=True)
    otp_code = StringField(required=True, max_length=10)
    expires_at = DateTimeField(required=True)
    is_used = BooleanField(default=False, required=True)
    created_at = DateTimeField(default=utc_now, required=True)

    @property
    def user(self):
        from app.models.user import User
        return User.objects(id=self.user_id).first()

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
        if self._data.get("id") is not None:
            try:
                self.save()
            except Exception:
                pass

    def __repr__(self) -> str:
        return f"<PasswordResetOTP user_id={self.user_id} used={self.is_used}>"
