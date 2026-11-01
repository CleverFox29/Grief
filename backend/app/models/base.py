"""Base declarations and reusable mixins for MongoEngine documents."""

from datetime import datetime, timezone
from mongoengine import DateTimeField

def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Mixin adding created_at and updated_at timestamps to entities."""
    created_at = DateTimeField(default=utc_now, required=True)
    updated_at = DateTimeField(default=utc_now, required=True)

    def clean(self):
        if hasattr(super(), "clean"):
            super().clean()
        self.updated_at = utc_now()
