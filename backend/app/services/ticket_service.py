"""Ticket management and lifecycle service (F4-F13)."""

import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, UploadFile
from mongoengine import Q

from app.models import (
    Ticket,
    TicketLog,
    Category,
    StaffRecord,
    Feedback,
    Notification,
    AuditLog,
    AuditAction,
    TicketStatus,
    User,
    UserRole
)
from app.core.upload import validate_and_save_photo
from app.config import settings
from app.schemas.ticket import (
    TicketItemResponse,
    TicketDetailResponse,
    TicketLogResponse,
    FeedbackResponse,
    SubmitFeedbackRequest,
    ReopenTicketRequest,
    UpdateTicketRequest
)

class TicketService:
    """Service encapsulating ticket creation, triage, queue filtering, feedback, and 7-day reopen loop."""

    @staticmethod
    def generate_ticket_id(db = None) -> str:
        """Generate unique ticket ID in format TKT-YYYY-XXXX (F5)."""
        year = datetime.now(timezone.utc).year
        count = Ticket.objects.count()
        sequence = count + 1
        return f"TKT-{year}-{sequence:04d}"

    @classmethod
    def create_ticket(
        cls,
        db,
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
        category = Category.objects(
            id=category_id,
            is_active=True
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
            parent = Ticket.objects(id=parent_ticket_id).first()
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
        # Embedding is computed once when the record is created, then reused for live searches.
        try:
            from app.services.deduplication_service import EmbeddingProvider
            new_ticket.description_embedding = EmbeddingProvider.encode(new_ticket.description) or []
        except Exception:
            new_ticket.description_embedding = []
        new_ticket.save()

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
        ticket_log.save()

        # Notify student
        notification = Notification(
            user_id=student.id,
            ticket_id=new_ticket.id,
            message=f"Your ticket #{new_ticket.ticket_id} ({category.name}) has been filed. Status: {new_ticket.status}."
        )
        notification.save()

        # System audit
        audit = AuditLog(
            user_id=student.id,
            action=AuditAction.TICKET_CREATED.value,
            entity_type="TICKET",
            entity_id=new_ticket.ticket_id,
            details=f"Ticket created in '{category.name}' at '{location}'. Status: {new_ticket.status}."
        )
        audit.save()

        return new_ticket

    @staticmethod
    def _calculate_reopen_status(t: Ticket) -> Tuple[bool, Optional[int]]:
        """Calculate if ticket is within 7-day reopen window and remaining days (F13)."""
        if t.status != TicketStatus.RESOLVED.value or not t.resolved_at:
            return False, None
        
        res_time = t.resolved_at
        if res_time.tzinfo is None:
            res_time = res_time.replace(tzinfo=timezone.utc)
            
        elapsed = datetime.now(timezone.utc) - res_time
        remaining_days = settings.REOPEN_WINDOW_DAYS - elapsed.days
        can_reopen = elapsed <= timedelta(days=settings.REOPEN_WINDOW_DAYS)
        return can_reopen, max(0, remaining_days) if can_reopen else 0

    @classmethod
    def _build_ticket_item_response(cls, t: Ticket) -> TicketItemResponse:
        """Helper to transform Ticket entity to TicketItemResponse with nested duplicates."""
        can_reopen, _ = cls._calculate_reopen_status(t)
        
        duplicate_children = []
        if t.duplicate_tickets:
            for child in t.duplicate_tickets:
                child_can_reopen, _ = cls._calculate_reopen_status(child)
                child_staff_name = child.assigned_staff.name if child.assigned_staff else None
                child_serviceman_name = child.assigned_serviceman.name if child.assigned_serviceman else None
                child_rating = child.student_rating or (child.feedback.rating if child.feedback else None)
                child_feedback = child.student_feedback or (child.feedback.comment if child.feedback else None)
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
                    assigned_staff_id=child.assigned_staff_id or child.assigned_serviceman_id,
                    assigned_staff_name=child_staff_name or child_serviceman_name,
                    assigned_serviceman_id=child.assigned_serviceman_id,
                    assigned_serviceman_name=child_serviceman_name,
                    scheduling_remark=child.scheduling_remark,
                    scheduled_at=child.scheduled_at,
                    proof_of_work_url=child.proof_of_work_url,
                    serviceman_remark=child.serviceman_remark,
                    student_rating=child_rating,
                    student_feedback=child_feedback,
                    resolved_at=child.resolved_at,
                    has_feedback=child.feedback is not None,
                    can_reopen=child_can_reopen,
                    created_at=child.created_at,
                    updated_at=child.updated_at,
                    duplicate_count=0,
                    duplicate_children=[]
                ))

        t_staff_name = t.assigned_staff.name if t.assigned_staff else None
        t_serviceman_name = t.assigned_serviceman.name if t.assigned_serviceman else None
        t_rating = t.student_rating or (t.feedback.rating if t.feedback else None)
        t_feedback = t.student_feedback or (t.feedback.comment if t.feedback else None)

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
            assigned_staff_id=t.assigned_staff_id or t.assigned_serviceman_id,
            assigned_staff_name=t_staff_name or t_serviceman_name,
            assigned_serviceman_id=t.assigned_serviceman_id,
            assigned_serviceman_name=t_serviceman_name,
            scheduling_remark=t.scheduling_remark,
            scheduled_at=t.scheduled_at,
            proof_of_work_url=t.proof_of_work_url,
            serviceman_remark=t.serviceman_remark,
            student_rating=t_rating,
            student_feedback=t_feedback,
            resolved_at=t.resolved_at,
            has_feedback=t.feedback is not None,
            can_reopen=can_reopen,
            created_at=t.created_at,
            updated_at=t.updated_at,
            duplicate_count=len(duplicate_children),
            duplicate_children=duplicate_children
        )

    @classmethod
    def get_student_tickets(
        cls,
        db,
        student_id: int,
        status_filter: Optional[str] = None,
        sort_order: str = "desc"
    ) -> List[TicketItemResponse]:
        """Retrieve all grievances filed by student, sorted by newest first (F8, U4)."""
        qs = Ticket.objects(student_id=student_id)

        if status_filter and status_filter.upper() != "ALL":
            qs = qs.filter(status=status_filter.upper())

        if sort_order == "asc":
            tickets = list(qs.order_by("+created_at", "+id"))
        else:
            tickets = list(qs.order_by("-created_at", "-id"))

        return [cls._build_ticket_item_response(t) for t in tickets]

    @classmethod
    def get_admin_queue(
        cls,
        db,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        location: Optional[str] = None,
        sort_by: str = "oldest_unresolved"
    ) -> List[TicketItemResponse]:
        """Unified queue of all campus tickets across all categories (F9, F10, U5)."""
        qs = Ticket.objects(parent_ticket_id=None)

        if search and search.strip():
            s = re.escape(search.strip())
            qs = qs.filter(
                Q(ticket_id__icontains=s) |
                Q(description__icontains=s) |
                Q(location__icontains=s)
            )

        if category_id:
            qs = qs.filter(category_id=category_id)

        if status_filter and status_filter.upper() != "ALL":
            qs = qs.filter(status=status_filter.upper())

        if location and location.strip():
            qs = qs.filter(location__icontains=re.escape(location.strip()))

        if sort_by == "newest":
            tickets = list(qs.order_by("-created_at", "-id"))
        elif sort_by == "oldest":
            tickets = list(qs.order_by("+created_at", "+id"))
        else:
            tickets = list(qs)
            unresolved = [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]
            tickets.sort(key=lambda t: (0 if t.status in unresolved else 1, t.created_at, t.id))

        return [cls._build_ticket_item_response(t) for t in tickets]

    @classmethod
    def get_ticket_detail(cls, db, ticket_id: int, current_user: User) -> TicketDetailResponse:
        """Retrieve complete ticket detail, timeline history, and feedback (F8, F13, U4, U7)."""
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        if current_user.role == UserRole.STUDENT.value:
            if ticket.student_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        if ticket.is_confidential and current_user.role != UserRole.ADMIN.value and ticket.student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This ticket is marked confidential.")

        if current_user.role == UserRole.SERVICEMAN.value:
            if ticket.is_confidential:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This ticket is marked confidential.")
            is_assigned = (ticket.assigned_serviceman_id == current_user.id or ticket.assigned_staff_id == current_user.id)
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: This ticket has not been assigned to you by an administrator."
                )

        # Timeline logs
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

        # Duplicate children
        duplicate_children = [cls._build_ticket_item_response(c) for c in ticket.duplicate_tickets]

        # Calculate reopen window
        can_reopen, remaining_days = cls._calculate_reopen_status(ticket)

        # Feedback
        feedback_resp = None
        if ticket.feedback:
            feedback_resp = FeedbackResponse(
                id=ticket.feedback.id,
                ticket_id=ticket.feedback.ticket_id,
                student_id=ticket.feedback.student_id,
                student_name=ticket.student.name if ticket.student else "",
                rating=ticket.feedback.rating,
                comment=ticket.feedback.comment,
                submitted_at=ticket.feedback.submitted_at
            )

        serviceman = ticket.assigned_serviceman
        serviceman_name = serviceman.name if serviceman else None
        serviceman_contact = getattr(serviceman, "phone", None) or getattr(serviceman, "phone_number", None)

        staff = ticket.assigned_staff
        staff_name = staff.name if staff else (serviceman_name if serviceman else None)
        staff_contact = getattr(staff, "contact", None) if staff else (serviceman_contact if serviceman else None)

        student_rating = ticket.student_rating or (ticket.feedback.rating if ticket.feedback else None)
        student_feedback = ticket.student_feedback or (ticket.feedback.comment if ticket.feedback else None)

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
            assigned_staff_id=ticket.assigned_staff_id or ticket.assigned_serviceman_id,
            assigned_staff_name=staff_name,
            assigned_staff_contact=staff_contact,
            assigned_serviceman_id=ticket.assigned_serviceman_id,
            assigned_serviceman_name=serviceman_name,
            assigned_serviceman_contact=serviceman_contact,
            scheduling_remark=ticket.scheduling_remark,
            scheduled_at=ticket.scheduled_at,
            proof_of_work_url=ticket.proof_of_work_url,
            serviceman_remark=ticket.serviceman_remark,
            student_rating=student_rating,
            student_feedback=student_feedback,
            resolved_at=ticket.resolved_at,
            closed_at=ticket.closed_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            can_reopen=can_reopen,
            reopen_remaining_days=remaining_days,
            feedback=feedback_resp,
            logs=logs_response,
            duplicate_children=duplicate_children
        )

    @classmethod
    def update_ticket(
        cls,
        db,
        admin_user: User,
        ticket_id: int,
        update_data: UpdateTicketRequest
    ) -> Ticket:
        """Update ticket status, assign maintenance worker, and add remark (F11, U6)."""
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        # Optimistic concurrency check
        if update_data.expected_updated_at:
            exp_time = update_data.expected_updated_at
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            curr_time = ticket.updated_at
            if curr_time.tzinfo is None:
                curr_time = curr_time.replace(tzinfo=timezone.utc)
            
            if abs((curr_time - exp_time).total_seconds()) > 1.0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This ticket was updated by another administrator. Please refresh the page before saving."
                )

        old_status = ticket.status
        status_changed = update_data.status and update_data.status != old_status
        staff_changed = False
        new_staff = None

        if update_data.assigned_staff_id is not None:
            if update_data.assigned_staff_id != ticket.assigned_staff_id:
                new_staff = StaffRecord.objects(
                    id=update_data.assigned_staff_id
                ).first()
                if not new_staff:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member record not found.")
                
                ticket.assigned_staff_id = new_staff.id
                staff_changed = True

        if getattr(update_data, "assigned_serviceman_id", None) is not None:
            if update_data.assigned_serviceman_id != ticket.assigned_serviceman_id:
                new_serviceman = User.objects(id=update_data.assigned_serviceman_id).first()
                if not new_serviceman:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviceman user not found.")
                ticket.assigned_serviceman_id = new_serviceman.id
                if not ticket.assigned_staff_id:
                    ticket.assigned_staff_id = new_serviceman.id
                staff_changed = True
                new_staff = new_serviceman
                if ticket.status == TicketStatus.OPEN.value and not update_data.status:
                    ticket.status = TicketStatus.IN_PROGRESS.value
                    status_changed = True

        now = datetime.now(timezone.utc)
        if status_changed:
            target_status = (update_data.status or ticket.status).upper()
            valid_statuses = [s.value for s in TicketStatus]
            if target_status not in valid_statuses:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {target_status}")

            ticket.status = target_status
            if target_status == TicketStatus.RESOLVED.value:
                ticket.resolved_at = now
            elif target_status == TicketStatus.CLOSED.value:
                ticket.closed_at = now

        ticket.save()

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
        log_entry.save()

        # Notify student (F12)
        notification = Notification(
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            message=f"Ticket #{ticket.ticket_id} update: Status is now '{ticket.status}'. Remark: {update_data.remark}"
        )
        notification.save()

        # Cascading closure (F11)
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
                child_log.save()
                
                child_notify = Notification(
                    user_id=child.student_id,
                    ticket_id=child.id,
                    message=f"Ticket #{child.ticket_id} (linked to parent #{ticket.ticket_id}) has been {ticket.status}."
                )
                child_notify.save()

        return ticket

    @classmethod
    def submit_feedback(
        cls,
        db,
        student_user: User,
        ticket_id: int,
        feedback_data: SubmitFeedbackRequest
    ) -> Feedback:
        """
        Record 1-5 star rating and comment on a RESOLVED grievance (F13, U7).
        """
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        # Ensure student owns the ticket
        if ticket.student_id != student_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only review your own tickets.")

        # Ensure status is RESOLVED or CLOSED
        if ticket.status not in [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feedback can only be submitted for RESOLVED or CLOSED tickets (current status: {ticket.status})."
            )

        # Upsert feedback
        existing_feedback = Feedback.objects(ticket_id=ticket.id).first()
        if existing_feedback:
            existing_feedback.rating = feedback_data.rating
            existing_feedback.comment = feedback_data.comment
            existing_feedback.save()
            feedback = existing_feedback
        else:
            feedback = Feedback(
                ticket_id=ticket.id,
                student_id=student_user.id,
                rating=feedback_data.rating,
                comment=feedback_data.comment
            )
            feedback.save()

        # Record in timeline
        log_entry = TicketLog(
            ticket_id=ticket.id,
            performed_by_id=student_user.id,
            action="FEEDBACK_SUBMITTED",
            old_status=ticket.status,
            new_status=ticket.status,
            remark=f"Student submitted {feedback_data.rating}★ rating. Comment: {feedback_data.comment or 'No comment'}"
        )
        log_entry.save()

        # System audit
        audit = AuditLog(
            user_id=student_user.id,
            action=AuditAction.FEEDBACK_SUBMITTED.value,
            entity_type="TICKET",
            entity_id=ticket.ticket_id,
            details=f"Rating {feedback_data.rating}/5 submitted on ticket #{ticket.ticket_id}."
        )
        audit.save()

        return feedback

    @classmethod
    def reopen_ticket(
        cls,
        db,
        student_user: User,
        ticket_id: int,
        reopen_data: ReopenTicketRequest
    ) -> Ticket:
        """
        Reopen a grievance within 7 days if the problem persists (F13, U7).
        """
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        if ticket.student_id != student_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only reopen your own tickets.")

        # Check eligibility and 7-day window (F13, U7 Exception)
        can_reopen, message = ticket.can_be_reopened()
        if not can_reopen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{message} If the problem persists, please raise a new ticket."
            )

        # Transition status to OPEN and clear resolved_at
        ticket.reopen(reason=reopen_data.reason)

        # Timeline entry
        log_entry = TicketLog(
            ticket_id=ticket.id,
            performed_by_id=student_user.id,
            action="TICKET_REOPENED",
            old_status=TicketStatus.RESOLVED.value,
            new_status=TicketStatus.OPEN.value,
            remark=f"Reopened by student: {reopen_data.reason.strip()}"
        )
        log_entry.save()

        # Notify student
        notification = Notification(
            user_id=student_user.id,
            ticket_id=ticket.id,
            message=f"Ticket #{ticket.ticket_id} has been reopened and placed back in the queue."
        )
        notification.save()

        # System audit
        audit = AuditLog(
            user_id=student_user.id,
            action=AuditAction.TICKET_REOPENED.value,
            entity_type="TICKET",
            entity_id=ticket.ticket_id,
            details=f"Ticket #{ticket.ticket_id} reopened by student. Reason: {reopen_data.reason.strip()}"
        )
        audit.save()

        return ticket

    @classmethod
    def get_serviceman_queue(
        cls,
        db,
        serviceman: User,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        assigned_only: bool = True
    ) -> List[TicketItemResponse]:
        """
        Retrieve tickets assigned to an authenticated serviceman.
        Tickets are strictly visible only after an administrator assigns them to this serviceman.
        """
        qs = Ticket.objects(
            Q(assigned_serviceman_id=serviceman.id) | Q(assigned_staff_id=serviceman.id)
        )

        if status_filter and status_filter.upper() != "ALL":
            qs = qs.filter(status=status_filter.upper())

        if search and search.strip():
            s = search.strip()
            qs = qs.filter(
                Q(ticket_id__icontains=s) |
                Q(location__icontains=s) |
                Q(description__icontains=s)
            )

        tickets = list(qs.order_by("-created_at", "-id"))
        return [cls._build_ticket_item_response(t) for t in tickets]

    @classmethod
    def claim_ticket(cls, db, ticket_id: int, serviceman: User) -> TicketDetailResponse:
        """Serviceman claims an open or available ticket and marks it IN PROGRESS."""
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        serviceman_cat = getattr(serviceman, "category", "") or ""
        ticket_cat = ticket.category.name if ticket.category else ""
        if serviceman_cat and ticket_cat and (serviceman_cat.strip().lower() != ticket_cat.strip().lower()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot claim ticket in '{ticket_cat}' category when registered for '{serviceman_cat}'."
            )

        old_status = ticket.status
        ticket.assigned_serviceman_id = serviceman.id
        if not ticket.assigned_staff_id:
            ticket.assigned_staff_id = serviceman.id
        if ticket.status == TicketStatus.OPEN.value:
            ticket.status = TicketStatus.IN_PROGRESS.value
        ticket.save()

        log = TicketLog(
            ticket_id=ticket.id,
            performed_by_id=serviceman.id,
            action="TICKET_CLAIMED",
            old_status=old_status,
            new_status=ticket.status,
            remark=f"Ticket claimed by serviceman {serviceman.name} ({serviceman_cat}). Status set to {ticket.status}."
        )
        log.save()

        notification = Notification(
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            message=f"Serviceman {serviceman.name} has claimed your grievance #{ticket.ticket_id} and started work."
        )
        notification.save()

        audit = AuditLog(
            user_id=serviceman.id,
            action=AuditAction.STATUS_CHANGED.value,
            entity_type="TICKET",
            entity_id=ticket.ticket_id,
            details=f"Serviceman {serviceman.name} claimed ticket #{ticket.ticket_id}. Status: {ticket.status}."
        )
        audit.save()

        return cls.get_ticket_detail(db, ticket.id, serviceman)

    @classmethod
    def schedule_visit(
        cls,
        db,
        ticket_id: int,
        serviceman: User,
        scheduling_remark: str
    ) -> TicketDetailResponse:
        """
        Serviceman acknowledges and records visit schedule note (e.g. 'I will come on Monday at 3 PM').
        Transitions status to IN_PROGRESS.
        Notifies the student.
        """
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        is_assigned = (ticket.assigned_serviceman_id == serviceman.id or ticket.assigned_staff_id == serviceman.id)
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only schedule visits for tickets assigned to you by an administrator."
            )

        old_status = ticket.status
        ticket.schedule_visit(
            serviceman_id=serviceman.id,
            scheduling_remark=scheduling_remark
        )

        log = TicketLog(
            ticket_id=ticket.id,
            performed_by_id=serviceman.id,
            action="VISIT_SCHEDULED",
            old_status=old_status,
            new_status=ticket.status,
            remark=f"Visit scheduled by {serviceman.name}: {scheduling_remark}"
        )
        log.save()

        notification = Notification(
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            message=f"Serviceman {serviceman.name} scheduled a visit for ticket #{ticket.ticket_id}: '{scheduling_remark}'"
        )
        notification.save()

        audit = AuditLog(
            user_id=serviceman.id,
            action=AuditAction.STATUS_CHANGED.value,
            entity_type="TICKET",
            entity_id=ticket.ticket_id,
            details=f"Serviceman {serviceman.name} scheduled visit on ticket #{ticket.ticket_id}: {scheduling_remark}"
        )
        audit.save()

        return cls.get_ticket_detail(db, ticket.id, serviceman)

    @classmethod
    def resolve_ticket_by_serviceman(
        cls,
        db,
        ticket_id: int,
        serviceman: User,
        remark: str,
        proof_file: Optional[UploadFile] = None,
        proof_url: Optional[str] = None
    ) -> TicketDetailResponse:
        """
        Serviceman submits proof of work and remarks.
        Ticket transitions from IN PROGRESS / OPEN -> PENDING CONFIRMATION.
        Student is notified to confirm or reopen.
        """
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        is_assigned = (ticket.assigned_serviceman_id == serviceman.id or ticket.assigned_staff_id == serviceman.id)
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only resolve tickets assigned to you by an administrator."
            )

        final_proof_url = proof_url
        if proof_file:
            final_proof_url = validate_and_save_photo(proof_file)

        old_status = ticket.status
        ticket.submit_proof_of_work(
            serviceman_id=serviceman.id,
            proof_url=final_proof_url,
            remark=remark
        )

        log = TicketLog(
            ticket_id=ticket.id,
            performed_by_id=serviceman.id,
            action="WORK_COMPLETED",
            old_status=old_status,
            new_status=TicketStatus.PENDING_CONFIRMATION.value,
            remark=f"Work completed: {remark}" + (f" (Proof: {final_proof_url})" if final_proof_url else "")
        )
        log.save()

        notification = Notification(
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            message=f"Serviceman {serviceman.name} marked ticket #{ticket.ticket_id} as fixed. Please review proof of work and confirm resolution."
        )
        notification.save()

        audit = AuditLog(
            user_id=serviceman.id,
            action=AuditAction.STATUS_CHANGED.value,
            entity_type="TICKET",
            entity_id=ticket.ticket_id,
            details=f"Serviceman {serviceman.name} submitted proof of work for ticket #{ticket.ticket_id}. Status: PENDING CONFIRMATION."
        )
        audit.save()

        return cls.get_ticket_detail(db, ticket.id, serviceman)

    @classmethod
    def confirm_ticket_resolution(
        cls,
        db,
        ticket_id: int,
        student: User,
        is_fixed: bool,
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> TicketDetailResponse:
        """
        Student verifies the work submitted by the serviceman.
        - If is_fixed=True: marks RESOLVED, records star rating (1-5) and feedback comment.
        - If is_fixed=False: rejects fix, transitions ticket back to OPEN / IN PROGRESS with reason.
        """
        ticket = Ticket.objects(id=ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        if ticket.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the student who raised this grievance can confirm resolution."
            )

        old_status = ticket.status

        if is_fixed:
            ticket.status = TicketStatus.RESOLVED.value
            ticket.resolved_at = datetime.now(timezone.utc)
            if rating is not None:
                ticket.student_rating = rating
            if feedback:
                ticket.student_feedback = feedback
            ticket.save()

            if rating is not None:
                existing_fb = Feedback.objects(ticket_id=ticket.id).first()
                if not existing_fb:
                    fb = Feedback(
                        ticket_id=ticket.id,
                        student_id=student.id,
                        rating=rating,
                        comment=feedback
                    )
                    fb.save()
                else:
                    existing_fb.rating = rating
                    existing_fb.comment = feedback
                    existing_fb.save()

            log = TicketLog(
                ticket_id=ticket.id,
                performed_by_id=student.id,
                action="RESOLUTION_CONFIRMED",
                old_status=old_status,
                new_status=TicketStatus.RESOLVED.value,
                remark=f"Student confirmed resolution (Rating: {rating or 'N/A'}/5). {feedback or ''}".strip()
            )
            log.save()

            if ticket.assigned_serviceman_id:
                notif = Notification(
                    user_id=ticket.assigned_serviceman_id,
                    ticket_id=ticket.id,
                    message=f"Student {student.name} confirmed resolution for #{ticket.ticket_id} with rating {rating or 5}/5!"
                )
                notif.save()

            audit = AuditLog(
                user_id=student.id,
                action=AuditAction.FEEDBACK_SUBMITTED.value,
                entity_type="TICKET",
                entity_id=ticket.ticket_id,
                details=f"Student confirmed resolution for #{ticket.ticket_id}. Rating: {rating}."
            )
            audit.save()

        else:
            ticket.status = TicketStatus.OPEN.value
            ticket.resolved_at = None
            ticket.student_feedback = feedback
            ticket.save()

            reject_remark = f"Student reported issue is NOT fixed: {feedback or 'No remark provided.'}"
            log = TicketLog(
                ticket_id=ticket.id,
                performed_by_id=student.id,
                action="RESOLUTION_REJECTED",
                old_status=old_status,
                new_status=TicketStatus.OPEN.value,
                remark=reject_remark
            )
            log.save()

            if ticket.assigned_serviceman_id:
                notif = Notification(
                    user_id=ticket.assigned_serviceman_id,
                    ticket_id=ticket.id,
                    message=f"Student {student.name} indicated #{ticket.ticket_id} was NOT resolved: {feedback or 'Issue persists.'}"
                )
                notif.save()

            audit = AuditLog(
                user_id=student.id,
                action=AuditAction.TICKET_REOPENED.value,
                entity_type="TICKET",
                entity_id=ticket.ticket_id,
                details=f"Student rejected fix for #{ticket.ticket_id}: {feedback}."
            )
            audit.save()

        return cls.get_ticket_detail(db, ticket.id, student)
