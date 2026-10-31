"""User entity hierarchy demonstrating OOP principles (User -> Student, Admin)."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base
from app.models.base import TimestampMixin, utc_now
from app.models.enums import UserRole
from app.core.security import hash_password, verify_password
from app.config import settings

class User(Base, TimestampMixin):
    """
    Base User entity.
    Encapsulates core authentication attributes, lockout logic, and credential management.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g. Student ID or Admin ID
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.STUDENT.value)
    
    # Account lockout & security tracking (F2)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Single Table Inheritance discriminator
    __mapper_args__ = {
        "polymorphic_on": role,
        "polymorphic_identity": "USER",
    }

    def set_password(self, plain_password: str) -> None:
        """Hash and update user's password."""
        self.password_hash = hash_password(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify plain password against stored hash."""
        return verify_password(plain_password, self.password_hash)

    def is_locked(self) -> bool:
        """Check if account is currently locked due to failed attempts (F2)."""
        if self.locked_until:
            current_time = datetime.now(timezone.utc)
            # Normalize naive datetime from SQLite if necessary
            lock_time = self.locked_until
            if lock_time.tzinfo is None:
                lock_time = lock_time.replace(tzinfo=timezone.utc)
            return current_time < lock_time
        return False

    def record_failed_attempt(self) -> bool:
        """
        Record a failed login attempt. Locks account for 15 minutes if attempts reach 5.
        Returns True if account became locked as a result.
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
            return True
        return False

    def reset_failed_attempts(self) -> None:
        """Reset failed login count and clear lock upon successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def can_view_confidential_tickets(self) -> bool:
        """Determine if user has privilege to view confidential grievances."""
        return self.role == UserRole.ADMIN.value


class Student(User):
    """
    Student entity inheriting from User.
    Represents enrolled students or campus residents raising grievances.
    """
    enrollment_no = Column(String(50), nullable=True)
    hostel_room = Column(String(50), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": UserRole.STUDENT.value,
    }

    def can_reopen_ticket(self, ticket) -> bool:
        """
        Student can reopen a ticket only if it belongs to them, is in RESOLVED status,
        and within the 7-day window (F13).
        """
        if ticket.student_id != self.id:
            return False
        return ticket.can_be_reopened()[0]

    def can_rate_ticket(self, ticket) -> bool:
        """Student can submit rating/feedback only on their own RESOLVED tickets (F13)."""
        return ticket.student_id == self.id and ticket.status == "RESOLVED"


class Admin(User):
    """
    Admin entity inheriting from User.
    Represents administrative staff managing tickets, assignments, categories, and logs.
    """
    department = Column(String(100), nullable=True)
    admin_level = Column(String(50), default="STANDARD", nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": UserRole.ADMIN.value,
    }

    def can_manage_categories(self) -> bool:
        """Admins have permission to manage grievance categories."""
        return True

    def can_view_all_tickets(self) -> bool:
        """Admins have visibility over the entire unified ticket queue."""
        return True
