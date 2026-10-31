"""TicketLog entity representing immutable ticket history and audit timeline."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import utc_now

class TicketLog(Base):
    """
    Immutable log record for every action/transition performed on a ticket (F11, F15, NFR 4.2).
    Captures actor, action, previous status, new status, timestamp, and optional remark.
    """
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action = Column(String(50), nullable=False)  # e.g. "STATUS_CHANGE", "ASSIGN_STAFF", "REOPEN", "DUPLICATE_LINK"
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    remark = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="logs")
    performed_by = relationship("User")

    def __repr__(self) -> str:
        return f"<TicketLog ticket_id={self.ticket_id} action='{self.action}' by_user={self.performed_by_id}>"
