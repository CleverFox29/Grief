"""StaffRecord entity representing campus maintenance/administrative personnel."""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class StaffRecord(Base, TimestampMixin):
    """
    Staff member record held in database for ticket assignment.
    Staff members do not log into the portal (SRS 1.3).
    """
    __tablename__ = "staff_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(50), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    category = relationship("Category", back_populates="staff_members")
    assigned_tickets = relationship("Ticket", back_populates="assigned_staff")

    def __repr__(self) -> str:
        return f"<StaffRecord id={self.id} name='{self.name}'>"
