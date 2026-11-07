"""Admin API endpoints for master records, CSV imports, auditing, and report exports (F14, F15, U8, U9)."""

import re
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Query, Response, status
from mongoengine import Q

from app.database import get_db
from app.core.deps import require_admin
from app.models import User, Student, StaffRecord, Category
from app.schemas.admin import (
    StudentCreateRequest,
    StudentResponse,
    CSVImportResponse,
    StaffCreateRequest,
    StaffUpdateRequest,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    AuditLogResponse,
    ReportResponse
)
from app.schemas.ticket import CategoryResponse, StaffResponse
from app.services.admin_service import AdminService
from app.services.deduplication_service import EmbeddingProvider

router = APIRouter(prefix="/admin", tags=["Admin Master Data & Reports"])


@router.post("/tickets/backfill-embeddings")
def backfill_ticket_embeddings(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
    db = Depends(get_db),
):
    """Admin-only bounded backfill for older ticket records missing Gemini vectors."""
    return EmbeddingProvider.backfill_missing(limit=limit)

# ------------------ Student Management (F14, U8) ------------------

@router.get("/students", response_model=List[StudentResponse])
def get_students(
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Retrieve list of registered students."""
    query = Student.objects
    if search and search.strip():
        s = re.escape(search.strip())
        query = query.filter(Q(user_id__icontains=s) | Q(name__icontains=s) | Q(email__icontains=s))
    students = query.order_by("-created_at").limit(100)
    return [
        StudentResponse(
            id=st.id,
            user_id=st.user_id,
            name=st.name,
            email=st.email,
            phone=st.phone,
            role=st.role,
            is_active=st.is_active,
            enrollment_no=getattr(st, "enrollment_no", None),
            hostel_room=getattr(st, "hostel_room", None)
        )
        for st in students
    ]

@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def add_student(
    request: StudentCreateRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Add a student record manually (F14, U8). Rejects duplicate IDs."""
    student = AdminService.create_student(db=db, admin_user=current_user, data=request)
    return student

@router.post("/students/import-csv", response_model=CSVImportResponse)
def import_students_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Bulk import student records from a CSV file (F14, U8)."""
    return AdminService.import_students_csv(db=db, admin_user=current_user, file=file)


# ------------------ Staff Records (F14, U8) ------------------

@router.post("/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    request: StaffCreateRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Create a new maintenance worker record (F14, U8)."""
    staff = AdminService.create_staff(db=db, admin_user=current_user, data=request)
    return StaffResponse(
        id=staff.id,
        name=staff.name,
        contact=staff.contact,
        category_id=staff.category_id,
        category_name=staff.category.name if staff.category else None,
        is_active=staff.is_active,
        notes=staff.notes
    )

@router.patch("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    request: StaffUpdateRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Update maintenance staff record."""
    staff = AdminService.update_staff(db=db, admin_user=current_user, staff_id=staff_id, data=request)
    return StaffResponse(
        id=staff.id,
        name=staff.name,
        contact=staff.contact,
        category_id=staff.category_id,
        category_name=staff.category.name if staff.category else None,
        is_active=staff.is_active,
        notes=staff.notes
    )


# ------------------ Category Management (F14, U8) ------------------

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    request: CategoryCreateRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Add a new grievance category (F14, U8)."""
    return AdminService.create_category(db=db, admin_user=current_user, data=request)

@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Edit grievance category name or description (F14, U8)."""
    return AdminService.update_category(db=db, admin_user=current_user, category_id=category_id, data=request)

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Delete a category (F14, U8).
    Safeguard: Blocked if category has open or in-progress tickets.
    """
    return AdminService.delete_category(db=db, admin_user=current_user, category_id=category_id)


# ------------------ Audit Logs & Reports (F15, U9) ------------------

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """View immutable system audit logs (F15, NFR 4.2). Non-editable."""
    return AdminService.get_audit_logs(db=db, limit=limit, action=action)

@router.get("/reports", response_model=ReportResponse)
def get_reports(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Retrieve aggregate summary of tickets by category and status (F15, U9)."""
    return AdminService.generate_report(db=db, start_date=start_date, end_date=end_date)

@router.get("/reports/export")
def export_reports_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Download ticket summary report as CSV file (F15)."""
    csv_data = AdminService.export_report_csv(db=db, start_date=start_date, end_date=end_date)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cgas_summary_report.csv"}
    )
