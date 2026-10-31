"""AuditLog entity representing immutable system-wide security and action logs."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import utc_now

class AuditLog(Base):
    """
    Immutable system-wide audit entry (F15, NFR 4.2).
    Captures user actions, administration modifications, CSV imports, category changes, and auth events.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)  # e.g. "TICKET", "CATEGORY", "STUDENT", "STAFF"
    entity_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog action='{self.action}' user_id={self.user_id} at={self.timestamp}>"
