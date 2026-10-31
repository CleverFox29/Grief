"""API endpoints for categories, duplicate checks, ticket tracking, admin queue, and triage (F4-F12)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user, require_student, require_admin
from app.models import User, Category, StaffRecord, Notification, Ticket
from app.schemas.ticket import (
    CategoryResponse,
    StaffResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    TicketResponse,
    TicketItemResponse,
    TicketDetailResponse,
    UpdateTicketRequest,
    NotificationResponse
)
from app.services.deduplication_service import DeduplicationEngine
from app.services.ticket_service import TicketService

router = APIRouter(prefix="", tags=["Grievances"])

# ----------------- Category & Staff Reference Endpoints -----------------

@router.get("/categories", response_model=List[CategoryResponse])
def get_active_categories(db: Session = Depends(get_db)):
    """Retrieve list of all active grievance categories (F4)."""
    return db.query(Category).filter(Category.is_active == True).order_by(Category.name.asc()).all()

@router.get("/staff", response_model=List[StaffResponse])
def get_staff_records(
    category_id: Optional[int] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve staff members for ticket assignment (Admin only)."""
    query = db.query(StaffRecord).filter(StaffRecord.is_active == True)
    if category_id:
        query = query.filter(StaffRecord.category_id == category_id)
    staff_list = query.order_by(StaffRecord.name.asc()).all()
    
    result = []
    for s in staff_list:
        result.append(StaffResponse(
            id=s.id,
            name=s.name,
            contact=s.contact,
            category_id=s.category_id,
            category_name=s.category.name if s.category else None,
            is_active=s.is_active,
            notes=s.notes
        ))
    return result


# ----------------- Duplicate Check & Grievance Creation -----------------

@router.post("/tickets/check-duplicates", response_model=DuplicateCheckResponse)
def check_ticket_duplicates(
    request: DuplicateCheckRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Real-time duplicate detection (< 2s) comparing open tickets (F6)."""
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
    action: str = Form("CREATE"),
    parent_ticket_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Submit a campus grievance ticket (F4, F5, F7, U3)."""
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


# ----------------- Ticket Tracking & Admin Queue -----------------

@router.get("/tickets/my-tickets", response_model=List[TicketItemResponse])
def get_my_tickets(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, IN PROGRESS, RESOLVED, CLOSED, DUPLICATE"),
    sort: str = Query("desc", description="Sort order: desc (newest first) or asc (oldest first)"),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Retrieve all tickets filed by authenticated student (F8, U4)."""
    return TicketService.get_student_tickets(
        db=db,
        student_id=current_user.id,
        status_filter=status,
        sort_order=sort
    )

@router.get("/tickets/admin-queue", response_model=List[TicketItemResponse])
def get_admin_ticket_queue(
    search: Optional[str] = Query(None, description="Search by Ticket ID, location or description"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    sort: str = Query("oldest_unresolved", description="Sort by: oldest_unresolved, newest, oldest"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Unified admin ticket queue across all categories with search and multi-filtering (F9, F10, U5).
    Duplicate tickets are returned grouped under their parent tickets.
    """
    return TicketService.get_admin_queue(
        db=db,
        search=search,
        category_id=category_id,
        status_filter=status,
        location=location,
        sort_by=sort
    )

@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_details(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve complete ticket detail and full timeline audit history (F8, U4, U6)."""
    return TicketService.get_ticket_detail(db=db, ticket_id=ticket_id, current_user=current_user)

@router.patch("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def update_ticket_triage(
    ticket_id: int,
    request: UpdateTicketRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update ticket status, assign staff member, and record mandatory remark (F11, U6).
    Cascades closure to duplicate child tickets.
    """
    updated_ticket = TicketService.update_ticket(
        db=db,
        admin_user=current_user,
        ticket_id=ticket_id,
        update_data=request
    )
    return TicketService.get_ticket_detail(db=db, ticket_id=updated_ticket.id, current_user=current_user)


# ----------------- Student Status Notifications -----------------

@router.get("/notifications", response_model=List[NotificationResponse])
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve notifications for the current authenticated user (F12)."""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(30).all()

    result = []
    for n in notifications:
        result.append(NotificationResponse(
            id=n.id,
            ticket_id=n.ticket_id,
            ticket_uid=n.ticket.ticket_id if n.ticket else None,
            message=n.message,
            is_read=n.is_read,
            created_at=n.created_at
        ))
    return result

@router.patch("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.mark_as_read()
        db.commit()
    return {"success": True}
