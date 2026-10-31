"""API endpoints for categories, duplicate checks, and ticket creation (F4, F5, F6, F7)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user, require_student
from app.models import User, Category, Ticket
from app.schemas.ticket import (
    CategoryResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    TicketResponse
)
from app.services.deduplication_service import DeduplicationEngine
from app.services.ticket_service import TicketService

router = APIRouter(prefix="", tags=["Grievances"])

@router.get("/categories", response_model=List[CategoryResponse])
def get_active_categories(db: Session = Depends(get_db)):
    """
    Retrieve list of all active grievance categories for ticket filing (F4).
    """
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.name.asc()).all()
    return categories

@router.post("/tickets/check-duplicates", response_model=DuplicateCheckResponse)
def check_ticket_duplicates(
    request: DuplicateCheckRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Real-time duplicate detection comparing against open tickets in the same category & location (F6).
    Enforces NFR 4.1 (< 2 second latency).
    """
    matches = DeduplicationEngine.check_duplicates(
        db=db,
        category_id=request.category_id,
        location=request.location,
        description=request.description
    )
    return DuplicateCheckResponse(
        has_duplicates=len(matches) > 0,
        count=len(matches),
        matches=matches
    )

@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def raise_grievance(
    category_id: int = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    is_confidential: bool = Form(False),
    action: str = Form("CREATE"),  # "CREATE", "SUPPORT", "SUBMIT_ANYWAY"
    parent_ticket_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Submit a campus grievance ticket (F4, F5, F7, U3).
    - F4: Category, location, description, optional photo (< 5MB JPG/PNG), optional confidential flag.
    - F5: Unique ticket ID (TKT-YYYY-XXXX), status OPEN.
    - F7: If action="SUPPORT", ticket created as DUPLICATE linked to parent. If "SUBMIT_ANYWAY", flagged OPEN.
    """
    ticket = TicketService.create_ticket(
        db=db,
        student=current_user,
        category_id=category_id,
        location=location,
        description=description,
        photo_file=photo,
        is_confidential=is_confidential,
        action=action,
        parent_ticket_id=parent_ticket_id
    )

    return TicketResponse(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        student_id=ticket.student_id,
        category_id=ticket.category_id,
        category_name=ticket.category.name if ticket.category else "",
        location=ticket.location,
        description=ticket.description,
        photo_url=ticket.photo_url,
        is_confidential=ticket.is_confidential,
        status=ticket.status,
        is_flagged_duplicate=ticket.is_flagged_duplicate,
        parent_ticket_id=ticket.parent_ticket_id,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )
