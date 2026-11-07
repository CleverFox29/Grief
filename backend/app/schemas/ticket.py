"""Pydantic schemas for ticket creation, duplicate checks, triage, timeline, staff, feedback, serviceman workflows, and reopening."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import TicketStatus

# ----------------- Category & Staff -----------------
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

# ----------------- Duplicate Detection -----------------
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

# ----------------- Timeline & Feedback -----------------
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

class FeedbackResponse(BaseModel):
    id: int
    ticket_id: int
    student_id: int
    student_name: str
    rating: int
    comment: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True

class SubmitFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating between 1 and 5 (F13)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional qualitative feedback")

class ReopenTicketRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Reason why grievance remains unresolved (F13)")

# ----------------- Serviceman & Student Actions -----------------
class TicketCreate(BaseModel):
    """Schema for a student raising a new grievance."""
    category_id: int = Field(..., description="ID of the grievance category")
    location: str = Field(..., max_length=150, description="Specific location on campus")
    description: str = Field(..., min_length=10, description="Detailed description of the issue")
    photo_url: Optional[str] = Field(None, description="URL of the uploaded grievance photo")
    is_confidential: bool = Field(False, description="If True, only admins can view details")

class ServicemanWorkSubmit(BaseModel):
    """Schema for a serviceman submitting their proof of work (F11.5)."""
    proof_of_work_url: Optional[str] = Field(None, description="URL of the uploaded proof image")
    serviceman_remark: str = Field(..., min_length=5, max_length=1000, description="Explanation of the fix")

class TicketResolveRequest(BaseModel):
    status: TicketStatus = Field(default=TicketStatus.PENDING_CONFIRMATION)
    serviceman_remark: str = Field(..., min_length=5, description="Explanation of the fix")
    proof_of_work_url: Optional[str] = Field(None, description="Optional proof of work URL")

class StudentConfirmRequest(BaseModel):
    """Schema for a student confirming or rejecting a serviceman's fix (F13)."""
    is_fixed: bool = Field(..., description="True to confirm resolution, False to reopen/reject")
    rating: Optional[int] = Field(None, ge=1, le=5, description="1 to 5 star rating (if fixed)")
    feedback: Optional[str] = Field(None, max_length=500, description="Optional written feedback or issue persistence reason")

class TicketUpdate(BaseModel):
    """Schema for an admin updating ticket properties."""
    assigned_serviceman_id: Optional[int] = Field(None, description="ID of the assigned Serviceman")
    status: Optional[str] = Field(None, description="Force update status")
    is_flagged_duplicate: Optional[bool] = None

class TicketLinkRequest(BaseModel):
    """Schema for linking a ticket as a duplicate."""
    parent_ticket_id: int = Field(..., description="ID of the parent ticket")

# ----------------- Ticket Responses -----------------
class TicketResponse(BaseModel):
    id: int
    ticket_id: str
    student_id: int
    category_id: int
    category_name: Optional[str] = None
    location: str
    description: str
    photo_url: Optional[str] = None
    is_confidential: bool
    status: str
    is_flagged_duplicate: bool
    parent_ticket_id: Optional[int] = None
    assigned_staff_id: Optional[int] = None
    assigned_serviceman_id: Optional[int] = None
    proof_of_work_url: Optional[str] = None
    serviceman_remark: Optional[str] = None
    student_rating: Optional[int] = None
    student_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

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
    assigned_serviceman_id: Optional[int] = None
    assigned_serviceman_name: Optional[str] = None
    proof_of_work_url: Optional[str] = None
    serviceman_remark: Optional[str] = None
    student_rating: Optional[int] = None
    student_feedback: Optional[str] = None
    resolved_at: Optional[datetime] = None
    has_feedback: bool = False
    can_reopen: bool = False
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
    assigned_serviceman_id: Optional[int] = None
    assigned_serviceman_name: Optional[str] = None
    assigned_serviceman_contact: Optional[str] = None
    proof_of_work_url: Optional[str] = None
    serviceman_remark: Optional[str] = None
    student_rating: Optional[int] = None
    student_feedback: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    can_reopen: bool = False
    reopen_remaining_days: Optional[int] = None
    feedback: Optional[FeedbackResponse] = None
    logs: List[TicketLogResponse] = []
    duplicate_children: List[TicketItemResponse] = []

    class Config:
        from_attributes = True

class TicketListResponse(BaseModel):
    """Schema for paginated ticket lists."""
    total: int
    tickets: List[TicketItemResponse]

class UpdateTicketRequest(BaseModel):
    status: Optional[str] = Field(None, description="New ticket status: OPEN, IN PROGRESS, PENDING CONFIRMATION, RESOLVED, CLOSED")
    assigned_staff_id: Optional[int] = Field(None, description="Staff member record ID to assign")
    assigned_serviceman_id: Optional[int] = Field(None, description="Serviceman user ID to assign")
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
