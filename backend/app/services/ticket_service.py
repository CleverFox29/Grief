"""Ticket management and lifecycle service (F4, F5, F7)."""

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Ticket, TicketLog, Category, Notification, AuditLog, AuditAction, TicketStatus, User
from app.core.upload import validate_and_save_photo

class TicketService:
    """Service encapsulating ticket creation, duplicate actions, and lifecycle auditing."""

    @staticmethod
    def generate_ticket_id(db: Session) -> str:
        """
        Generate unique ticket ID in format TKT-YYYY-XXXX (F5).
        """
        year = datetime.now(timezone.utc).year
        # Count existing tickets created in current year
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
        action: str = "CREATE",  # "CREATE", "SUPPORT", "SUBMIT_ANYWAY"
        parent_ticket_id: Optional[int] = None
    ) -> Ticket:
        """
        Create a new campus grievance according to F4, F5, and F7.
        """
        # Validate category exists and is active
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.is_active == True
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {category_id} is either invalid or inactive."
            )

        # Validate mandatory fields
        if not location.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location is required.")
        if not description.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description is required.")

        # Validate & store photo if provided (F4, NFR 4.2)
        photo_url = validate_and_save_photo(photo_file)

        # Generate unique ticket ID and timestamp
        ticket_uid = cls.generate_ticket_id(db)
        
        # Determine initial status and parent linkage (F7)
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
        db.flush()  # Generate primary key

        # Create initial audit log on the ticket (F11, NFR 4.2)
        if action == "SUPPORT" and parent:
            ticket_log = TicketLog(
                ticket_id=new_ticket.id,
                performed_by_id=student.id,
                action="DUPLICATE_LINKED",
                old_status=None,
                new_status=TicketStatus.DUPLICATE.value,
                remark=f"Supported existing issue #{parent.ticket_id}. Linked as child duplicate."
            )
        else:
            ticket_log = TicketLog(
                ticket_id=new_ticket.id,
                performed_by_id=student.id,
                action="TICKET_CREATED",
                old_status=None,
                new_status=TicketStatus.OPEN.value,
                remark="Grievance filed by student." + (" [Flagged by student as submit anyway]" if is_flagged else "")
            )
        db.add(ticket_log)

        # Send confirmation notification to student (F12)
        notification_msg = (
            f"Your ticket #{new_ticket.ticket_id} for {category.name} has been filed successfully. "
            f"Status: {new_ticket.status}."
        )
        notification = Notification(
            user_id=student.id,
            ticket_id=new_ticket.id,
            message=notification_msg
        )
        db.add(notification)

        # System-level audit entry (F15)
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
