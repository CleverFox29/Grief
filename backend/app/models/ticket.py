"""Ticket entity representing student grievances and complete lifecycle state."""

import weakref
from datetime import datetime, timedelta, timezone
from typing import Tuple, List, Optional
from mongoengine import (
    Document,
    StringField,
    IntField,
    BooleanField,
    DateTimeField,
    SequenceField
)
from app.models.base import TimestampMixin, utc_now
from app.models.enums import TicketStatus
from app.config import settings

class Ticket(Document, TimestampMixin):
    """
    Ticket entity representing a campus grievance (F4, F5).
    Maintains lifecycle status, assignment, duplicate linkages, and confidentiality.
    """
    meta = {
        "collection": "tickets",
        "indexes": [
            "ticket_id",
            "student_id",
            "category_id",
            "assigned_staff_id",
            "parent_ticket_id",
            "location",
            "status",
            "-created_at"
        ]
    }

    _registry = weakref.WeakValueDictionary()

    id = SequenceField(primary_key=True)
    ticket_id = StringField(required=True, unique=True, max_length=50)  # e.g. "TKT-2026-0001"
    
    student_id = IntField(required=True)
    category_id = IntField(required=True)
    assigned_staff_id = IntField(null=True)
    parent_ticket_id = IntField(null=True)
    
    location = StringField(required=True, max_length=150)
    description = StringField(required=True)
    photo_url = StringField(max_length=255, null=True)
    is_confidential = BooleanField(default=False, required=True)
    status = StringField(default=TicketStatus.OPEN.value, required=True, max_length=20)
    is_flagged_duplicate = BooleanField(default=False, required=True)
    
    resolved_at = DateTimeField(null=True)
    closed_at = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        res = super().save(*args, **kwargs)
        if self._data.get("id") is not None:
            self._registry[self.id] = self
        return res

    @classmethod
    def _from_son(cls, son, _auto_dereference=True, created=False):
        doc = super()._from_son(son, _auto_dereference=_auto_dereference, created=created)
        if doc.id in cls._registry:
            existing = cls._registry[doc.id]
            for k, v in doc._data.items():
                existing._data[k] = v
            return existing
        cls._registry[doc.id] = doc
        return doc

    # Relationships as dynamic properties
    @property
    def student(self):
        from app.models.user import User
        return User.objects(id=self.student_id).first()

    @property
    def category(self):
        from app.models.category import Category
        return Category.objects(id=self.category_id).first()

    @property
    def assigned_staff(self):
        if self.assigned_staff_id:
            from app.models.staff import StaffRecord
            return StaffRecord.objects(id=self.assigned_staff_id).first()
        return None

    @property
    def parent_ticket(self):
        if self.parent_ticket_id:
            return Ticket.objects(id=self.parent_ticket_id).first()
        return None

    @property
    def duplicate_tickets(self) -> List["Ticket"]:
        return list(Ticket.objects(parent_ticket_id=self.id))

    @property
    def logs(self) -> List:
        from app.models.ticket_log import TicketLog
        return list(TicketLog.objects(ticket_id=self.id).order_by("-timestamp"))

    @property
    def feedback(self):
        from app.models.feedback import Feedback
        return Feedback.objects(ticket_id=self.id).first()

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
        if self._data.get("id") is not None:
            self.save()

    def link_to_parent(self, parent: "Ticket") -> None:
        """
        Link this ticket as a child DUPLICATE of a parent ticket (F7).
        """
        self.parent_ticket_id = parent.id
        self.status = TicketStatus.DUPLICATE.value
        if self._data.get("id") is not None:
            self.save()

    def cascade_close(self, closed_by_user_id: int, remark: str = "Closed automatically with parent ticket.") -> List["Ticket"]:
        """
        Close this parent ticket and cascade closure to all linked duplicate tickets (F11).
        Returns the list of affected duplicate tickets.
        """
        now = datetime.now(timezone.utc)
        self.status = TicketStatus.CLOSED.value
        self.closed_at = now
        self.save()
        
        closed_children = []
        for child in self.duplicate_tickets:
            if child.status != TicketStatus.CLOSED.value:
                child.status = TicketStatus.CLOSED.value
                child.closed_at = now
                child.save()
                closed_children.append(child)
                
        return closed_children

    def __repr__(self) -> str:
        return f"<Ticket {self.ticket_id} status='{self.status}' category_id={self.category_id}>"
