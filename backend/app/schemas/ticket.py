"""Pydantic schemas for ticket creation, duplicate checks, triage, timeline, and staff."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class StaffResponse(BaseModel):
    id: int
    name: str
    contact: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class DuplicateCheckRequest(BaseModel):
    category_id: int = Field(..., description="ID of grievance category")
    location: str = Field(..., min_length=2, description="Campus location or room")
    description: str = Field(..., min_length=5, description="Issue description")

class DuplicateMatch(BaseModel):
    id: int
    ticket_id: str
    category_id: int
    category_name: str
    location: str
    description: str
    status: str
    similarity_score: float
    created_at: Optional[str] = None

class DuplicateCheckResponse(BaseModel):
    has_duplicates: bool
    count: int
    matches: List[DuplicateMatch]

class TicketResponse(BaseModel):
    id: int
    ticket_id: str
    student_id: int
    category_id: int
    category_name: str
    location: str
    description: str
    photo_url: Optional[str] = None
    is_confidential: bool
    status: str
    is_flagged_duplicate: bool
    parent_ticket_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketLogResponse(BaseModel):
    id: int
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    remark: Optional[str] = None
    performed_by_name: str
    performed_by_role: str
    timestamp: datetime

    class Config:
        from_attributes = True

class TicketItemResponse(BaseModel):
    id: int
    ticket_id: str
    student_id: int
    student_name: str
    category_id: int
    category_name: str
    location: str
    description: str
    photo_url: Optional[str] = None
    is_confidential: bool
    status: str
    is_flagged_duplicate: bool
    parent_ticket_id: Optional[int] = None
    assigned_staff_id: Optional[int] = None
    assigned_staff_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    duplicate_count: int = 0
    duplicate_children: List["TicketItemResponse"] = []

    class Config:
        from_attributes = True

class TicketDetailResponse(BaseModel):
    id: int
    ticket_id: str
    student_id: int
    student_name: str
    student_email: str
    student_phone: Optional[str] = None
    student_room: Optional[str] = None
    category_id: int
    category_name: str
    location: str
    description: str
    photo_url: Optional[str] = None
    is_confidential: bool
    status: str
    is_flagged_duplicate: bool
    parent_ticket_id: Optional[int] = None
    parent_ticket_uid: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    assigned_staff_name: Optional[str] = None
    assigned_staff_contact: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    logs: List[TicketLogResponse] = []
    duplicate_children: List[TicketItemResponse] = []

    class Config:
        from_attributes = True

class UpdateTicketRequest(BaseModel):
    status: Optional[str] = Field(None, description="New ticket status: OPEN, IN PROGRESS, RESOLVED, CLOSED")
    assigned_staff_id: Optional[int] = Field(None, description="Staff member record ID to assign")
    remark: str = Field(..., min_length=1, description="Mandatory remark explaining this update (F11)")
    expected_updated_at: Optional[datetime] = Field(None, description="Optimistic concurrency check timestamp")

class NotificationResponse(BaseModel):
    id: int
    ticket_id: int
    ticket_uid: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
