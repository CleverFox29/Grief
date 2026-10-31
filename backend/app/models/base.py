"""Base declarations and reusable mixins."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime

def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Mixin adding created_at and updated_at timestamps to entities."""
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
