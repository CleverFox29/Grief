"""Pydantic schemas for master records, CSV uploads, audit logs, and reports (F14, F15)."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class StudentCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=2, max_length=50, description="Student Enrollment ID")
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=6, description="Initial account password")
    enrollment_no: Optional[str] = None
    hostel_room: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    enrollment_no: Optional[str] = None
    hostel_room: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CSVImportResponse(BaseModel):
    total_processed: int
    successfully_imported: int
    duplicates_rejected: int
    errors: List[str] = []
    message: str

class StaffCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    contact: str = Field(..., min_length=5, max_length=50)
    category_id: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None

class StaffUpdateRequest(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class ServicemanCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=2, max_length=50, description="Serviceman User ID")
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    category: str = Field(..., min_length=2, max_length=50, description="Trade/Category Name (e.g. Administrative, Carpentry)")
    phone: Optional[str] = None
    password: Optional[str] = Field("Serviceman@123", min_length=6, description="Initial account password")

class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ReportSummaryItem(BaseModel):
    category_id: int
    category_name: str
    open_count: int
    in_progress_count: int
    resolved_count: int
    closed_count: int
    duplicate_count: int
    total_count: int

class ReportResponse(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_tickets: int
    total_open: int
    total_in_progress: int
    total_resolved: int
    total_closed: int
    total_duplicate: int
    summary: List[ReportSummaryItem]
