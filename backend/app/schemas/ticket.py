"""Pydantic schemas for ticket creation, duplicate checks, and category listing."""

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
