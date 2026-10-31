"""Ticket entity representing student grievances and complete lifecycle state."""

from datetime import datetime, timedelta, timezone
from typing import Tuple, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, utc_now
from app.models.enums import TicketStatus
from app.config import settings

class Ticket(Base, TimestampMixin):
    """
    Ticket entity representing a campus grievance (F4, F5).
    Maintains lifecycle status, assignment, duplicate linkages, and confidentiality.
    """
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g. "TKT-2026-0001"
    
    # Foreign keys
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("staff_records.id"), nullable=True)
    parent_ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)
    
    # Details
    location = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)
    photo_url = Column(String(255), nullable=True)
    is_confidential = Column(Boolean, default=False, nullable=False)  # Visible only to admins (F4)
    status = Column(String(20), default=TicketStatus.OPEN.value, nullable=False, index=True)
    is_flagged_duplicate = Column(Boolean, default=False, nullable=False)  # Submitted anyway flag (F7)
    
    # Timestamps for lifecycle milestones
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("User", foreign_keys=[student_id], backref="filed_tickets")
    category = relationship("Category", back_populates="tickets")
    assigned_staff = relationship("StaffRecord", back_populates="assigned_tickets")
    
    # Self-referencing relationship for duplicate linking (F7, F11)
    parent_ticket = relationship("Ticket", remote_side=[id], backref="duplicate_tickets")
    
    # Timeline and feedback
    logs = relationship("TicketLog", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketLog.timestamp.desc()")
    feedback = relationship("Feedback", back_populates="ticket", uselist=False, cascade="all, delete-orphan")

    def is_duplicate(self) -> bool:
        """Return True if this ticket is linked as a duplicate of another ticket."""
        return self.status == TicketStatus.DUPLICATE.value or self.parent_ticket_id is not None

    def is_parent(self) -> bool:
        """Return True if other duplicate tickets are linked to this parent ticket."""
        return len(self.duplicate_tickets) > 0

    def can_be_reopened(self) -> Tuple[bool, str]:
        """
        Check if student can reopen ticket within 7-day window (F13 / U7).
        """
        if self.status != TicketStatus.RESOLVED.value:
            return False, f"Only tickets in RESOLVED status can be reopened (current: {self.status})."
        
        if not self.resolved_at:
            return False, "Ticket has no recorded resolution timestamp."
        
        # Calculate time elapsed since resolution
        res_time = self.resolved_at
        if res_time.tzinfo is None:
            res_time = res_time.replace(tzinfo=timezone.utc)
        
        current_time = datetime.now(timezone.utc)
        delta = current_time - res_time
        
        if delta > timedelta(days=settings.REOPEN_WINDOW_DAYS):
            return False, f"Reopen window exceeded. Tickets cannot be reopened after {settings.REOPEN_WINDOW_DAYS} days."
        
        return True, "Ticket is eligible for reopening."

    def reopen(self, reason: str) -> None:
        """
        Reopen the ticket, resetting status to OPEN (F13).
        """
        allowed, message = self.can_be_reopened()
        if not allowed:
            raise ValueError(message)
        
        self.status = TicketStatus.OPEN.value
        self.resolved_at = None

    def link_to_parent(self, parent: "Ticket") -> None:
        """
        Link this ticket as a child DUPLICATE of a parent ticket (F7).
        """
        self.parent_ticket_id = parent.id
        self.status = TicketStatus.DUPLICATE.value

    def cascade_close(self, closed_by_user_id: int, remark: str = "Closed automatically with parent ticket.") -> List["Ticket"]:
        """
        Close this parent ticket and cascade closure to all linked duplicate tickets (F11).
        Returns the list of affected duplicate tickets.
        """
        now = datetime.now(timezone.utc)
        self.status = TicketStatus.CLOSED.value
        self.closed_at = now
        
        closed_children = []
        for child in self.duplicate_tickets:
            if child.status != TicketStatus.CLOSED.value:
                child.status = TicketStatus.CLOSED.value
                child.closed_at = now
                closed_children.append(child)
                
        return closed_children

    def __repr__(self) -> str:
        return f"<Ticket {self.ticket_id} status='{self.status}' category_id={self.category_id}>"
