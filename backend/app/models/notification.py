"""Notification entity representing student status alerts."""

from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, SequenceField
from app.models.base import utc_now

class Notification(Document):
    """
    Notification sent to student on ticket status transitions (F12).
    """
    meta = {
        "collection": "notifications",
        "indexes": [
            "user_id",
            "ticket_id",
            "is_read",
            "-created_at"
        ]
    }

    id = SequenceField(primary_key=True)
    user_id = IntField(required=True)
    ticket_id = IntField(required=True)
    message = StringField(required=True)
    is_read = BooleanField(default=False, required=True)
    created_at = DateTimeField(default=utc_now, required=True)

    @property
    def user(self):
        from app.models.user import User
        return User.objects(id=self.user_id).first()

    @property
    def ticket(self):
        from app.models.ticket import Ticket
        return Ticket.objects(id=self.ticket_id).first()

    def mark_as_read(self) -> None:
        """Mark notification as read by user."""
        self.is_read = True
        self.save()

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} read={self.is_read}>"
