"""TicketLog entity representing immutable ticket history and audit timeline."""

from mongoengine import Document, StringField, IntField, DateTimeField, SequenceField
from app.models.base import utc_now

class TicketLog(Document):
    """
    Immutable log record for every action/transition performed on a ticket (F11, F15, NFR 4.2).
    Captures actor, action, previous status, new status, timestamp, and optional remark.
    """
    meta = {
        "collection": "ticket_logs",
        "indexes": [
            "ticket_id",
            "performed_by_id",
            "-timestamp"
        ]
    }

    id = SequenceField(primary_key=True)
    ticket_id = IntField(required=True)
    performed_by_id = IntField(required=True)
    
    action = StringField(required=True, max_length=50)  # e.g. "STATUS_CHANGE", "ASSIGN_STAFF", "REOPEN", "DUPLICATE_LINK"
    old_status = StringField(max_length=20, null=True)
    new_status = StringField(max_length=20, null=True)
    remark = StringField(null=True)
    timestamp = DateTimeField(default=utc_now, required=True)

    @property
    def ticket(self):
        from app.models.ticket import Ticket
        return Ticket.objects(id=self.ticket_id).first()

    @property
    def performed_by(self):
        from app.models.user import User
        return User.objects(id=self.performed_by_id).first()

    def __repr__(self) -> str:
        return f"<TicketLog ticket_id={self.ticket_id} action='{self.action}' by_user={self.performed_by_id}>"
