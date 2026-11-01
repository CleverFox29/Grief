"""Category entity representing grievance categories."""

from typing import Tuple, List
from mongoengine import Document, StringField, BooleanField, SequenceField
from app.models.base import TimestampMixin
from app.models.enums import TicketStatus

class Category(Document, TimestampMixin):
    """
    Grievance Category entity (e.g. Plumbing, Electrical, Carpentry, Masonry, Administrative, Security).
    """
    meta = {
        "collection": "categories",
        "indexes": ["name", "is_active"]
    }

    id = SequenceField(primary_key=True)
    name = StringField(required=True, unique=True, max_length=50)
    description = StringField(null=True)
    is_active = BooleanField(default=True, required=True)

    @property
    def tickets(self) -> List:
        """Return tickets belonging to this category."""
        from app.models.ticket import Ticket
        return list(Ticket.objects(category_id=self.id))

    @property
    def staff_members(self) -> List:
        """Return staff members assigned to this category."""
        from app.models.staff import StaffRecord
        return list(StaffRecord.objects(category_id=self.id))

    def has_active_tickets(self) -> bool:
        """Check if category has unresolved (OPEN or IN PROGRESS) tickets."""
        from app.models.ticket import Ticket
        active_statuses = [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]
        return Ticket.objects(category_id=self.id, status__in=active_statuses).count() > 0

    def can_be_deleted(self) -> Tuple[bool, str]:
        """
        Enforce business rule (F14 / U8): A category with open tickets cannot be deleted.
        """
        if self.has_active_tickets():
            return False, f"Category '{self.name}' has active open/in-progress tickets and cannot be deleted."
        return True, "Category can be safely deleted."

    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}'>"
