"""Ticket management and lifecycle service (F4, F5, F7, F8, F9, F10, F11, F12)."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case

from app.models import (
    Ticket,
    TicketLog,
    Category,
    StaffRecord,
    Notification,
    AuditLog,
    AuditAction,
    TicketStatus,
    User,
    UserRole
)
from app.core.upload import validate_and_save_photo
from app.schemas.ticket import (
    TicketItemResponse,
    TicketDetailResponse,
    TicketLogResponse,
    UpdateTicketRequest
)

class TicketService:
    """Service encapsulating ticket creation, triage, queue filtering, and cascading closures."""

    @staticmethod
    def generate_ticket_id(db: Session) -> str:
        """Generate unique ticket ID in format TKT-YYYY-XXXX (F5)."""
        year = datetime.now(timezone.utc).year
        count = db.query(func.count(Ticket.id)).scalar() or 0
        sequence = count + 1
        return f"TKT-{year}-{sequence:04d}"

    @classmethod
    def create_ticket(
        cls,
        db: Session,
        student: User,
        category_id: int,
        location: str,
        description: str,
        photo_file: Optional[UploadFile] = None,
        is_confidential: bool = False,
        action: str = "CREATE",
        parent_ticket_id: Optional[int] = None
    ) -> Ticket:
        """Create a new campus grievance according to F4, F5, and F7."""
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.is_active == True
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {category_id} is either invalid or inactive."
            )

        if not location.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location is required.")
        if not description.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description is required.")

        photo_url = validate_and_save_photo(photo_file)
        ticket_uid = cls.generate_ticket_id(db)
        
        initial_status = TicketStatus.OPEN.value
        is_flagged = False
        parent = None

        if action == "SUPPORT":
            if not parent_ticket_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent ticket ID must be provided when supporting an existing ticket."
                )
            parent = db.query(Ticket).filter(Ticket.id == parent_ticket_id).first()
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent ticket not found.")
            initial_status = TicketStatus.DUPLICATE.value
        elif action == "SUBMIT_ANYWAY":
            is_flagged = True

        new_ticket = Ticket(
            ticket_id=ticket_uid,
            student_id=student.id,
            category_id=category.id,
            location=location.strip(),
            description=description.strip(),
            photo_url=photo_url,
            is_confidential=is_confidential,
            status=initial_status,
            is_flagged_duplicate=is_flagged,
            parent_ticket_id=parent.id if parent else None
        )
        db.add(new_ticket)
        db.flush()

        # Initial timeline entry
        if action == "SUPPORT" and parent:
            ticket_log = TicketLog(
                ticket_id=new_ticket.id,
                performed_by_id=student.id,
                action="DUPLICATE_LINKED",
                old_status=None,
                new_status=TicketStatus.DUPLICATE.value,
                remark=f"Supported existing grievance #{parent.ticket_id}. Linked as duplicate child."
            )
        else:
            ticket_log = TicketLog(
                ticket_id=new_ticket.id,
                performed_by_id=student.id,
                action="TICKET_CREATED",
                old_status=None,
                new_status=TicketStatus.OPEN.value,
                remark="Grievance filed by student." + (" [Flagged as submit anyway]" if is_flagged else "")
            )
        db.add(ticket_log)

        # Notify student
        notification = Notification(
            user_id=student.id,
            ticket_id=new_ticket.id,
            message=f"Your ticket #{new_ticket.ticket_id} ({category.name}) has been filed. Status: {new_ticket.status}."
        )
        db.add(notification)

        # System audit
        audit = AuditLog(
            user_id=student.id,
            action=AuditAction.TICKET_CREATED.value,
            entity_type="TICKET",
            entity_id=new_ticket.ticket_id,
            details=f"Ticket created in '{category.name}' at '{location}'. Status: {new_ticket.status}."
        )
        db.add(audit)

        db.commit()
        db.refresh(new_ticket)
        return new_ticket

    @staticmethod
    def _build_ticket_item_response(t: Ticket) -> TicketItemResponse:
        """Helper to transform Ticket entity to TicketItemResponse with nested duplicates."""
        duplicate_children = []
        if t.duplicate_tickets:
            for child in t.duplicate_tickets:
                duplicate_children.append(TicketItemResponse(
                    id=child.id,
                    ticket_id=child.ticket_id,
                    student_id=child.student_id,
                    student_name=child.student.name if child.student else "",
                    category_id=child.category_id,
                    category_name=child.category.name if child.category else "",
                    location=child.location,
                    description=child.description,
                    photo_url=child.photo_url,
                    is_confidential=child.is_confidential,
                    status=child.status,
                    is_flagged_duplicate=child.is_flagged_duplicate,
                    parent_ticket_id=child.parent_ticket_id,
                    assigned_staff_id=child.assigned_staff_id,
                    assigned_staff_name=child.assigned_staff.name if child.assigned_staff else None,
                    created_at=child.created_at,
                    updated_at=child.updated_at,
                    duplicate_count=0,
                    duplicate_children=[]
                ))

        return TicketItemResponse(
            id=t.id,
            ticket_id=t.ticket_id,
            student_id=t.student_id,
            student_name=t.student.name if t.student else "",
            category_id=t.category_id,
            category_name=t.category.name if t.category else "",
            location=t.location,
            description=t.description,
            photo_url=t.photo_url,
            is_confidential=t.is_confidential,
            status=t.status,
            is_flagged_duplicate=t.is_flagged_duplicate,
            parent_ticket_id=t.parent_ticket_id,
            assigned_staff_id=t.assigned_staff_id,
            assigned_staff_name=t.assigned_staff.name if t.assigned_staff else None,
            created_at=t.created_at,
            updated_at=t.updated_at,
            duplicate_count=len(duplicate_children),
            duplicate_children=duplicate_children
        )

    @classmethod
    def get_student_tickets(
        cls,
        db: Session,
        student_id: int,
        status_filter: Optional[str] = None,
        sort_order: str = "desc"
    ) -> List[TicketItemResponse]:
        """
        Retrieve all grievances filed by student, sorted by newest first (F8, U4).
        """
        query = db.query(Ticket).filter(Ticket.student_id == student_id)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(Ticket.status == status_filter.upper())

        if sort_order == "asc":
            query = query.order_by(Ticket.created_at.asc())
        else:
            query = query.order_by(Ticket.created_at.desc())

        tickets = query.all()
        return [cls._build_ticket_item_response(t) for t in tickets]

    @classmethod
    def get_admin_queue(
        cls,
        db: Session,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        location: Optional[str] = None,
        sort_by: str = "oldest_unresolved"
    ) -> List[TicketItemResponse]:
        """
        Unified queue of all campus tickets across all categories (F9, F10, U5).
        Groups duplicate tickets under parent tickets.
        """
        # Primary queue displays top-level tickets; child duplicates are embedded under parents
        query = db.query(Ticket).filter(Ticket.parent_ticket_id.is_(None))

        # Search by Ticket ID or text (F9)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(or_(
                Ticket.ticket_id.ilike(term),
                Ticket.description.ilike(term),
                Ticket.location.ilike(term)
            ))

        # Filter by category (F10)
        if category_id:
            query = query.filter(Ticket.category_id == category_id)

        # Filter by status (F10)
        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(Ticket.status == status_filter.upper())

        # Filter by location (F10)
        if location and location.strip():
            query = query.filter(Ticket.location.ilike(f"%{location.strip()}%"))

        # Sorting rules (F10, U5)
        if sort_by == "newest":
            query = query.order_by(Ticket.created_at.desc())
        elif sort_by == "oldest":
            query = query.order_by(Ticket.created_at.asc())
        else:
            # "oldest_unresolved" (U5 default: oldest unresolved first)
            # Unresolved tickets (OPEN, IN PROGRESS) come before RESOLVED and CLOSED
            is_unresolved = case(
                (Ticket.status.in_([TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]), 0),
                else_=1
            )
            query = query.order_by(is_unresolved.asc(), Ticket.created_at.asc())

        tickets = query.all()
        return [cls._build_ticket_item_response(t) for t in tickets]

    @classmethod
    def get_ticket_detail(cls, db: Session, ticket_id: int, current_user: User) -> TicketDetailResponse:
        """
        Retrieve complete ticket details and full timeline history (F8, U4, U6).
        Enforces confidentiality and ownership checks.
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        # Security check: Students can only view their own tickets (NFR 4.2)
        if current_user.role == UserRole.STUDENT.value:
            if ticket.student_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        # Confidentiality check: Confidential tickets are visible only to Admins (or author)
        if ticket.is_confidential and current_user.role != UserRole.ADMIN.value and ticket.student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This ticket is marked confidential.")

        # Build timeline logs
        logs_response = []
        for log in ticket.logs:
            performer = log.performed_by
            logs_response.append(TicketLogResponse(
                id=log.id,
                action=log.action,
                old_status=log.old_status,
                new_status=log.new_status,
                remark=log.remark,
                performed_by_name=performer.name if performer else "System",
                performed_by_role=performer.role if performer else "SYSTEM",
                timestamp=log.timestamp
            ))

        # Build nested duplicate children
        duplicate_children = [cls._build_ticket_item_response(c) for c in ticket.duplicate_tickets]

        return TicketDetailResponse(
            id=ticket.id,
            ticket_id=ticket.ticket_id,
            student_id=ticket.student_id,
            student_name=ticket.student.name if ticket.student else "",
            student_email=ticket.student.email if ticket.student else "",
            student_phone=ticket.student.phone if ticket.student else None,
            student_room=getattr(ticket.student, "hostel_room", None),
            category_id=ticket.category_id,
            category_name=ticket.category.name if ticket.category else "",
            location=ticket.location,
            description=ticket.description,
            photo_url=ticket.photo_url,
            is_confidential=ticket.is_confidential,
            status=ticket.status,
            is_flagged_duplicate=ticket.is_flagged_duplicate,
            parent_ticket_id=ticket.parent_ticket_id,
            parent_ticket_uid=ticket.parent_ticket.ticket_id if ticket.parent_ticket else None,
            assigned_staff_id=ticket.assigned_staff_id,
            assigned_staff_name=ticket.assigned_staff.name if ticket.assigned_staff else None,
            assigned_staff_contact=ticket.assigned_staff.contact if ticket.assigned_staff else None,
            resolved_at=ticket.resolved_at,
            closed_at=ticket.closed_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            logs=logs_response,
            duplicate_children=duplicate_children
        )

    @classmethod
    def update_ticket(
        cls,
        db: Session,
        admin_user: User,
        ticket_id: int,
        update_data: UpdateTicketRequest
    ) -> Ticket:
        """
        Update ticket status, assign maintenance worker, and add remark (F11, U6).
        Cascades closure to all child duplicates when parent is closed.
        Enforces optimistic concurrency control.
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        # Optimistic concurrency check (U6 Exception: Two admins edit same ticket)
        if update_data.expected_updated_at:
            exp_time = update_data.expected_updated_at
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            curr_time = ticket.updated_at
            if curr_time.tzinfo is None:
                curr_time = curr_time.replace(tzinfo=timezone.utc)
            
            # If difference > 1 second, reject save
            if abs((curr_time - exp_time).total_seconds()) > 1.0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This ticket was updated by another administrator. Please refresh the page before saving."
                )

        old_status = ticket.status
        status_changed = update_data.status and update_data.status != old_status
        staff_changed = False
        new_staff = None

        # 1. Update Staff Assignment
        if update_data.assigned_staff_id is not None:
            if update_data.assigned_staff_id != ticket.assigned_staff_id:
                new_staff = db.query(StaffRecord).filter(
                    StaffRecord.id == update_data.assigned_staff_id
                ).first()
                if not new_staff:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member record not found.")
                
                ticket.assigned_staff_id = new_staff.id
                staff_changed = True

        # 2. Update Status Transitions
        now = datetime.now(timezone.utc)
        if status_changed:
            target_status = update_data.status.upper()
            valid_statuses = [s.value for s in TicketStatus]
            if target_status not in valid_statuses:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {target_status}")

            ticket.status = target_status
            if target_status == TicketStatus.RESOLVED.value:
                ticket.resolved_at = now
            elif target_status == TicketStatus.CLOSED.value:
                ticket.closed_at = now

        # 3. Create TicketLog entry (F11, NFR 4.2)
        action_name = "STATUS_UPDATE" if status_changed else ("ASSIGN_STAFF" if staff_changed else "ADMIN_REMARK")
        remark_text = update_data.remark.strip()
        if staff_changed and new_staff:
            remark_text = f"Assigned to staff: {new_staff.name}. {remark_text}"

        log_entry = TicketLog(
            ticket_id=ticket.id,
            performed_by_id=admin_user.id,
            action=action_name,
            old_status=old_status,
            new_status=ticket.status,
            remark=remark_text
        )
        db.add(log_entry)

        # 4. Dispatch Student Notification (F12)
        notification_msg = (
            f"Ticket #{ticket.ticket_id} update: Status is now '{ticket.status}'. "
            f"Remark: {update_data.remark}"
        )
        notification = Notification(
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            message=notification_msg
        )
        db.add(notification)

        # 5. Cascading closure to duplicate tickets (F11)
        if status_changed and ticket.status in [TicketStatus.CLOSED.value, TicketStatus.RESOLVED.value]:
            closed_children = ticket.cascade_close(
                closed_by_user_id=admin_user.id,
                remark=f"Cascaded from parent #{ticket.ticket_id} ({ticket.status})."
            )
            for child in closed_children:
                child_log = TicketLog(
                    ticket_id=child.id,
                    performed_by_id=admin_user.id,
                    action="STATUS_UPDATE",
                    old_status=TicketStatus.DUPLICATE.value,
                    new_status=child.status,
                    remark=f"Closed automatically because parent ticket #{ticket.ticket_id} was {ticket.status}."
                )
                db.add(child_log)
                
                child_notify = Notification(
                    user_id=child.student_id,
                    ticket_id=child.id,
                    message=f"Ticket #{child.ticket_id} (linked to parent #{ticket.ticket_id}) has been {ticket.status}."
                )
                db.add(child_notify)

        db.commit()
        db.refresh(ticket)
        return ticket
