"""AuditLog entity representing immutable system-wide security and action logs."""

from mongoengine import Document, StringField, IntField, DateTimeField, SequenceField
from app.models.base import utc_now

class AuditLog(Document):
    """
    Immutable system-wide audit entry (F15, NFR 4.2).
    Captures user actions, administration modifications, CSV imports, category changes, and auth events.
    """
    meta = {
        "collection": "audit_logs",
        "indexes": [
            "user_id",
            "action",
            "entity_type",
            "-timestamp"
        ]
    }

    id = SequenceField(primary_key=True)
    user_id = IntField(null=True)
    action = StringField(required=True, max_length=50)
    entity_type = StringField(max_length=50, null=True)  # e.g. "TICKET", "CATEGORY", "STUDENT", "STAFF"
    entity_id = StringField(max_length=50, null=True)
    details = StringField(null=True)
    ip_address = StringField(max_length=50, null=True)
    timestamp = DateTimeField(default=utc_now, required=True)

    @property
    def user(self):
        if self.user_id:
            from app.models.user import User
            return User.objects(id=self.user_id).first()
        return None

    def __repr__(self) -> str:
        return f"<AuditLog action='{self.action}' user_id={self.user_id} at={self.timestamp}>"
