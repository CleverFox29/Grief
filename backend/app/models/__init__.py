"""OOP Domain and database models for CGAS."""

from app.models.enums import UserRole, TicketStatus, AuditAction
from app.models.base import TimestampMixin, utc_now
from app.models.user import User, Student, Admin, Serviceman
from app.models.staff import StaffRecord
from app.models.category import Category
from app.models.ticket import Ticket
from app.models.ticket_log import TicketLog
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.otp import PasswordResetOTP

__all__ = [
    "UserRole",
    "TicketStatus",
    "AuditAction",
    "TimestampMixin",
    "utc_now",
    "User",
    "Student",
    "Admin",
    "Serviceman",
    "StaffRecord",
    "Category",
    "Ticket",
    "TicketLog",
    "Feedback",
    "Notification",
    "AuditLog",
    "PasswordResetOTP",
]
