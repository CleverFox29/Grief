"""Category entity representing grievance categories."""

from typing import Tuple
from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import TicketStatus

class Category(Base, TimestampMixin):
    """
    Grievance Category entity (e.g. Plumbing, Electrical, Carpentry, Masonry, Administrative, Security).
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tickets = relationship("Ticket", back_populates="category")
    staff_members = relationship("StaffRecord", back_populates="category")

    def has_active_tickets(self) -> bool:
        """Check if category has unresolved (OPEN or IN PROGRESS) tickets."""
        active_statuses = {TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value}
        return any(t.status in active_statuses for t in self.tickets)

    def can_be_deleted(self) -> Tuple[bool, str]:
        """
        Enforce business rule (F14 / U8): A category with open tickets cannot be deleted.
        """
        if self.has_active_tickets():
            return False, f"Category '{self.name}' has active open/in-progress tickets and cannot be deleted."
        return True, "Category can be safely deleted."

    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}'>"
