"""User entity hierarchy demonstrating OOP principles (User -> Student, Admin)."""

from datetime import datetime, timedelta, timezone
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, SequenceField
from app.models.base import TimestampMixin, utc_now
from app.models.enums import UserRole
from app.core.security import hash_password, verify_password
from app.config import settings

class User(Document, TimestampMixin):
    """
    Base User entity.
    Encapsulates core authentication attributes, lockout logic, and credential management.
    """
    meta = {
        "collection": "users",
        "allow_inheritance": True,
        "indexes": [
            "user_id",
            "email",
            "role"
        ]
    }

    id = SequenceField(primary_key=True)
    user_id = StringField(required=True, unique=True, max_length=50)  # e.g. Student ID or Admin ID
    name = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True, max_length=120)
    phone = StringField(max_length=20, null=True)
    password_hash = StringField(required=True, max_length=255)
    role = StringField(required=True, default=UserRole.STUDENT.value, max_length=20)
    
    # Account lockout & security tracking (F2)
    failed_login_attempts = IntField(default=0, required=True)
    locked_until = DateTimeField(null=True)
    is_active = BooleanField(default=True, required=True)

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
    enrollment_no = StringField(max_length=50, null=True)
    hostel_room = StringField(max_length=50, null=True)

    def __init__(self, *args, **kwargs):
        if "role" not in kwargs:
            kwargs["role"] = UserRole.STUDENT.value
        super().__init__(*args, **kwargs)

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
    department = StringField(max_length=100, null=True)
    admin_level = StringField(default="STANDARD", max_length=50, null=True)

    def __init__(self, *args, **kwargs):
        if "role" not in kwargs:
            kwargs["role"] = UserRole.ADMIN.value
        super().__init__(*args, **kwargs)

    def can_manage_categories(self) -> bool:
        """Admins have permission to manage grievance categories."""
        return True

    def can_view_all_tickets(self) -> bool:
        """Admins have visibility over the entire unified ticket queue."""
        return True


class Serviceman(User):
    """
    Serviceman entity inheriting from User.
    Represents maintenance staff (e.g., Carpenters, Plumbers) who progress and resolve assigned tickets.
    """
    category = StringField(required=True, max_length=100)  # e.g., "Carpentry", "Plumbing"

    def __init__(self, *args, **kwargs):
        if "role" not in kwargs:
            kwargs["role"] = UserRole.SERVICEMAN.value
        if "phone_number" in kwargs and "phone" not in kwargs:
            kwargs["phone"] = kwargs.pop("phone_number")
        super().__init__(*args, **kwargs)

    @property
    def phone_number(self) -> Optional[str]:
        return self.phone

    @phone_number.setter
    def phone_number(self, value: Optional[str]) -> None:
        self.phone = value

    def can_resolve_ticket(self, ticket) -> bool:
        """
        Servicemen can only resolve tickets that are explicitly assigned to them 
        by an administrator and match their specific service category.
        """
        assigned_id = getattr(ticket, "assigned_serviceman_id", None) or getattr(ticket, "assigned_staff_id", None)
        if not assigned_id or assigned_id != self.id:
            return False

        ticket_cat = ticket.category.name if getattr(ticket, "category", None) else None
        if ticket_cat and self.category:
            return ticket_cat.strip().lower() == self.category.strip().lower()

        return True
