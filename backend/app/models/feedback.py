"""Feedback entity representing student rating and remarks on resolved grievances."""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import utc_now

class Feedback(Base):
    """
    Student rating and feedback submitted on a RESOLVED grievance (F13 / U7).
    Rating must be between 1 and 5.
    """
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_valid_rating_range"),
    )

    # Relationships
    ticket = relationship("Ticket", back_populates="feedback")
    student = relationship("User")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.rating is not None and not (1 <= self.rating <= 5):
            raise ValueError(f"Rating must be an integer between 1 and 5. Received: {self.rating}")

    def __repr__(self) -> str:
        return f"<Feedback ticket_id={self.ticket_id} rating={self.rating}>"
