"""Feedback entity representing student rating and remarks on resolved grievances."""

from mongoengine import Document, StringField, IntField, DateTimeField, SequenceField
from app.models.base import utc_now

class Feedback(Document):
    """
    Student rating and feedback submitted on a RESOLVED grievance (F13 / U7).
    Rating must be between 1 and 5.
    """
    meta = {
        "collection": "feedbacks",
        "indexes": [
            "ticket_id",
            "student_id",
            "-submitted_at"
        ]
    }

    id = SequenceField(primary_key=True)
    ticket_id = IntField(required=True, unique=True)
    student_id = IntField(required=True)
    
    rating = IntField(required=True, min_value=1, max_value=5)
    comment = StringField(null=True)
    submitted_at = DateTimeField(default=utc_now, required=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.rating is not None and not (1 <= self.rating <= 5):
            raise ValueError(f"Rating must be an integer between 1 and 5. Received: {self.rating}")

    @property
    def ticket(self):
        from app.models.ticket import Ticket
        return Ticket.objects(id=self.ticket_id).first()

    @property
    def student(self):
        from app.models.user import User
        return User.objects(id=self.student_id).first()

    def __repr__(self) -> str:
        return f"<Feedback ticket_id={self.ticket_id} rating={self.rating}>"
