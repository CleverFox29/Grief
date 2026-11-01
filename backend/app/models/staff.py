"""StaffRecord entity representing campus maintenance/administrative personnel."""

from mongoengine import Document, StringField, BooleanField, IntField, SequenceField
from app.models.base import TimestampMixin

class StaffRecord(Document, TimestampMixin):
    """
    Staff member record held in database for ticket assignment.
    Staff members do not log into the portal (SRS 1.3).
    """
    meta = {
        "collection": "staff_records",
        "indexes": ["name", "category_id", "is_active"]
    }

    id = SequenceField(primary_key=True)
    name = StringField(required=True, max_length=100)
    contact = StringField(required=True, max_length=50)
    category_id = IntField(null=True)
    is_active = BooleanField(default=True, required=True)
    notes = StringField(null=True)

    @property
    def category(self):
        """Reference to associated Category."""
        if self.category_id:
            from app.models.category import Category
            return Category.objects(id=self.category_id).first()
        return None

    @property
    def assigned_tickets(self):
        """Tickets assigned to this staff member."""
        from app.models.ticket import Ticket
        return list(Ticket.objects(assigned_staff_id=self.id))

    def __repr__(self) -> str:
        return f"<StaffRecord id={self.id} name='{self.name}'>"
