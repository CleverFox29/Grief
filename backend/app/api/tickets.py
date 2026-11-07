"""API endpoints for categories, duplicate checks, ticket tracking, admin queue, and triage (F4-F12)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, Query, status, HTTPException

from app.database import get_db
from app.core.deps import get_current_user, require_student, require_admin, require_serviceman, require_serviceman_or_admin
from app.models import User, Category, StaffRecord, Notification, Ticket, Serviceman
from app.schemas.ticket import (
    CategoryResponse,
    StaffResponse,
    ServicemanResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    TicketResponse,
    TicketItemResponse,
    TicketDetailResponse,
    UpdateTicketRequest,
    NotificationResponse,
    FeedbackResponse,
    SubmitFeedbackRequest,
    ReopenTicketRequest,
    TicketScheduleRequest,
    TicketCloseRequest,
    TicketResolveRequest,
    StudentConfirmRequest,
    ServicemanWorkSubmit
)
from app.services.deduplication_service import DeduplicationEngine
from app.services.ticket_service import TicketService

router = APIRouter(prefix="", tags=["Grievances"])

# ----------------- Category & Staff Reference Endpoints -----------------

@router.get("/categories", response_model=List[CategoryResponse])
def get_active_categories(db = Depends(get_db)):
    """Retrieve list of all active grievance categories (F4)."""
    categories = Category.objects(is_active=True).order_by("+name")
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            is_active=c.is_active
        )
        for c in categories
    ]

@router.get("/staff", response_model=List[StaffResponse])
def get_staff_records(
    category_id: Optional[int] = None,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Retrieve staff members for ticket assignment (Admin only)."""
    query = StaffRecord.objects(is_active=True)
    if category_id:
        query = query.filter(category_id=category_id)
    staff_list = query.order_by("+name")
    
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

@router.get("/servicemen", response_model=List[ServicemanResponse])
def get_servicemen(
    category: Optional[str] = Query(None, description="Filter by serviceman trade/category"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve active servicemen, optionally filtered by category (Admin & Servicemen)."""
    qs = Serviceman.objects(is_active=True)
    if category and category.strip():
        qs = qs.filter(category__iexact=category.strip())
    servicemen = qs.order_by("+name")
    return [
        ServicemanResponse(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            category=getattr(s, "category", "") or "",
            phone=s.phone,
            email=s.email,
            is_active=s.is_active
        )
        for s in servicemen
    ]


# ----------------- Duplicate Check & Grievance Creation -----------------

@router.post("/tickets/check-duplicates", response_model=DuplicateCheckResponse)
def check_ticket_duplicates(
    request: DuplicateCheckRequest,
    current_user: User = Depends(require_student),
    db = Depends(get_db)
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

@router.get("/tickets/suggestions", response_model=DuplicateCheckResponse)
def suggest_ticket_duplicates(
    category_id: int = Query(..., gt=0),
    location: str = Query("", max_length=150),
    query: str = Query(..., min_length=1, max_length=1000),
    current_user: User = Depends(require_student),
    db = Depends(get_db),
):
    """Live as-you-type suggestions for unresolved, non-confidential tickets."""
    matches = DeduplicationEngine.check_duplicates(
        db, category_id, location, query, limit=5,
        threshold=DeduplicationEngine.LIVE_SUGGESTION_THRESHOLD,
    )
    return DuplicateCheckResponse(has_duplicates=bool(matches), count=len(matches), matches=matches)


@router.get("/tickets/category-suggestion")
def suggest_ticket_category(
    query: str = Query(..., min_length=1, max_length=1000),
    current_user: User = Depends(require_student),
    db = Depends(get_db),
):
    """Suggest the best active category for the issue description."""
    categories = list(Category.objects(is_active=True).order_by("+name"))
    from app.services.deduplication_service import EmbeddingProvider
    result = EmbeddingProvider.suggest_category(query, categories)
    return {"suggestion": result}

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
    db = Depends(get_db)
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
    db = Depends(get_db)
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
    db = Depends(get_db)
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

@router.get("/tickets/serviceman-queue", response_model=List[TicketItemResponse])
def get_serviceman_queue(
    search: Optional[str] = Query(None, description="Search by Ticket ID, location or description"),
    status_filter: Optional[str] = Query(None, description="Filter by status (OPEN, IN PROGRESS, PENDING CONFIRMATION, RESOLVED, CLOSED, or ALL)"),
    assigned_only: bool = Query(False, description="Filter to only tickets assigned to this serviceman"),
    current_user: User = Depends(require_serviceman),
    db = Depends(get_db)
):
    """Retrieve ticket queue for authenticated serviceman filtered to their trade category."""
    return TicketService.get_serviceman_queue(
        db=db,
        serviceman=current_user,
        search=search,
        status_filter=status_filter,
        assigned_only=assigned_only
    )

@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_details(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Retrieve complete ticket detail and full timeline audit history (F8, U4, U6)."""
    return TicketService.get_ticket_detail(db=db, ticket_id=ticket_id, current_user=current_user)

@router.patch("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def update_ticket_triage(
    ticket_id: int,
    request: UpdateTicketRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
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
    db = Depends(get_db)
):
    """Retrieve notifications for the current authenticated user (F12)."""
    notifications = Notification.objects(
        user_id=current_user.id
    ).order_by("-created_at").limit(30)

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
    db = Depends(get_db)
):
    """Mark a notification as read."""
    notif = Notification.objects(
        id=notification_id,
        user_id=current_user.id
    ).first()
    if notif:
        notif.mark_as_read()
    return {"success": True}


# ----------------- Student Feedback & 7-Day Reopen (F13, U7) -----------------

@router.post("/tickets/{ticket_id}/feedback", response_model=FeedbackResponse)
def submit_ticket_feedback(
    ticket_id: int,
    request: SubmitFeedbackRequest,
    current_user: User = Depends(require_student),
    db = Depends(get_db)
):
    """
    Submit rating (1-5) and feedback comments on a RESOLVED grievance (F13, U7).
    """
    feedback = TicketService.submit_feedback(
        db=db,
        student_user=current_user,
        ticket_id=ticket_id,
        feedback_data=request
    )
    return FeedbackResponse(
        id=feedback.id,
        ticket_id=feedback.ticket_id,
        student_id=feedback.student_id,
        student_name=current_user.name,
        rating=feedback.rating,
        comment=feedback.comment,
        submitted_at=feedback.submitted_at
    )

@router.post("/tickets/{ticket_id}/reopen", response_model=TicketDetailResponse)
def reopen_grievance(
    ticket_id: int,
    request: ReopenTicketRequest,
    current_user: User = Depends(require_student),
    db = Depends(get_db)
):
    """
    Reopen a RESOLVED grievance within 7 days if problem persists (F13, U7).
    Disables and rejects reopening once 7 days have passed.
    """
    reopened = TicketService.reopen_ticket(
        db=db,
        student_user=current_user,
        ticket_id=ticket_id,
        reopen_data=request
    )
    return TicketService.get_ticket_detail(db=db, ticket_id=reopened.id, current_user=current_user)

# ----------------- Serviceman & Resolution Workflow Endpoints -----------------

@router.post("/tickets/{ticket_id}/claim", response_model=TicketDetailResponse)
def claim_ticket(
    ticket_id: int,
    current_user: User = Depends(require_serviceman),
    db = Depends(get_db)
):
    """Serviceman claims an available ticket in their category and marks it IN PROGRESS."""
    return TicketService.claim_ticket(
        db=db,
        ticket_id=ticket_id,
        serviceman=current_user
    )

@router.post("/tickets/{ticket_id}/schedule", response_model=TicketDetailResponse)
def schedule_ticket_visit(
    ticket_id: int,
    request: TicketScheduleRequest,
    current_user: User = Depends(require_serviceman),
    db = Depends(get_db)
):
    """Serviceman schedules visit with a remark (e.g. 'I will come on Monday at 3 PM') and marks IN PROGRESS."""
    return TicketService.schedule_visit(
        db=db,
        ticket_id=ticket_id,
        serviceman=current_user,
        scheduling_remark=request.scheduling_remark
    )

@router.post("/tickets/{ticket_id}/resolve", response_model=TicketDetailResponse)
def resolve_ticket(
    ticket_id: int,
    request: TicketResolveRequest,
    current_user: User = Depends(require_serviceman),
    db = Depends(get_db)
):
    """Serviceman resolves ticket with remarks and optional proof URL, moving status to PENDING CONFIRMATION."""
    return TicketService.resolve_ticket_by_serviceman(
        db=db,
        ticket_id=ticket_id,
        serviceman=current_user,
        remark=request.serviceman_remark,
        proof_url=request.proof_of_work_url
    )

@router.post("/tickets/{ticket_id}/submit-proof", response_model=TicketDetailResponse)
async def submit_proof_multipart(
    ticket_id: int,
    remark: str = Form(..., min_length=3),
    proof_url: Optional[str] = Form(None),
    proof_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_serviceman),
    db = Depends(get_db)
):
    """Serviceman submits proof photo file upload or URL with remarks, moving to PENDING CONFIRMATION."""
    return TicketService.resolve_ticket_by_serviceman(
        db=db,
        ticket_id=ticket_id,
        serviceman=current_user,
        remark=remark,
        proof_file=proof_file,
        proof_url=proof_url
    )

@router.post("/tickets/{ticket_id}/confirm", response_model=TicketDetailResponse)
def confirm_resolution(
    ticket_id: int,
    request: StudentConfirmRequest,
    current_user: User = Depends(require_student),
    db = Depends(get_db)
):
    """Student confirms or rejects the fix submitted by the serviceman."""
    return TicketService.confirm_ticket_resolution(
        db=db,
        ticket_id=ticket_id,
        student=current_user,
        is_fixed=request.is_fixed,
        rating=request.rating,
        feedback=request.feedback
    )

@router.post("/tickets/{ticket_id}/close", response_model=TicketDetailResponse)
def admin_manual_close(
    ticket_id: int,
    request: TicketCloseRequest,
    current_user: User = Depends(require_admin),
    db = Depends(get_db)
):
    """Admin manually closes any ticket at any point in its lifecycle (F11 / manual closure)."""
    update_data = UpdateTicketRequest(
        status="CLOSED",
        remark=request.remark
    )
    TicketService.update_ticket(
        db=db,
        admin_user=current_user,
        ticket_id=ticket_id,
        update_data=update_data
    )
    return TicketService.get_ticket_detail(db=db, ticket_id=ticket_id, current_user=current_user)
