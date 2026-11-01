"""Administrative service for master records, CSV uploads, auditing, and reporting (F14, F15)."""

import csv
import io
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status, UploadFile
from mongoengine import Q

from app.models import (
    User,
    Student,
    Admin,
    StaffRecord,
    Category,
    Ticket,
    TicketStatus,
    AuditLog,
    AuditAction,
    UserRole
)
from app.core.security import hash_password
from app.schemas.admin import (
    StudentCreateRequest,
    StudentResponse,
    CSVImportResponse,
    StaffCreateRequest,
    StaffUpdateRequest,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    AuditLogResponse,
    ReportSummaryItem,
    ReportResponse
)

class AdminService:
    """Service handling master data CRUD, CSV bulk import, immutable auditing, and report exports."""

    # ------------------ Student Master Records (F14) ------------------

    @classmethod
    def create_student(cls, db, admin_user: User, data: StudentCreateRequest) -> Student:
        """Add a single student record with duplicate ID prevention (F14, U8)."""
        existing_id = User.objects(user_id=data.user_id.strip()).first()
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A user with ID '{data.user_id}' already exists. Duplicate student IDs are rejected."
            )

        existing_email = User.objects(email=str(data.email).strip().lower()).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A user with email '{data.email}' already exists."
            )

        student = Student(
            user_id=data.user_id.strip(),
            name=data.name.strip(),
            email=str(data.email).strip().lower(),
            phone=data.phone.strip() if data.phone else None,
            password_hash=hash_password(data.password),
            role=UserRole.STUDENT.value,
            enrollment_no=data.enrollment_no.strip() if data.enrollment_no else data.user_id.strip(),
            hostel_room=data.hostel_room.strip() if data.hostel_room else None
        )
        student.save()

        audit = AuditLog(
            user_id=admin_user.id,
            action="STUDENT_CREATED",
            entity_type="STUDENT",
            entity_id=student.user_id,
            details=f"Student record created: {student.name} ({student.user_id})."
        )
        audit.save()

        return student

    @classmethod
    def import_students_csv(cls, db, admin_user: User, file: UploadFile) -> CSVImportResponse:
        """
        Bulk import student records from CSV file (F14, U8).
        Validates structure and rejects duplicate student IDs.
        """
        try:
            contents = file.file.read().decode("utf-8-sig")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to read CSV file. Please upload a valid UTF-8 text file. Error: {str(e)}"
            )

        reader = csv.DictReader(io.StringIO(contents))
        if not reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or invalid header format."
            )

        # Normalize field names
        field_map = {f.strip().lower(): f for f in reader.fieldnames}
        id_field = field_map.get("user_id") or field_map.get("student_id") or field_map.get("id") or field_map.get("enrollment_no")
        name_field = field_map.get("name") or field_map.get("student_name")
        email_field = field_map.get("email") or field_map.get("email_address")
        phone_field = field_map.get("phone") or field_map.get("mobile")
        password_field = field_map.get("password") or field_map.get("pass")
        room_field = field_map.get("hostel_room") or field_map.get("room")

        if not id_field or not name_field or not email_field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV must contain columns for User ID, Name, and Email. Found: {list(reader.fieldnames)}"
            )

        total_processed = 0
        imported_count = 0
        duplicates_rejected = 0
        errors = []
        seen_ids = set()

        for idx, row in enumerate(reader, start=2):
            total_processed += 1
            user_id = row.get(id_field, "").strip()
            name = row.get(name_field, "").strip()
            email = row.get(email_field, "").strip().lower()
            phone = row.get(phone_field, "").strip() if phone_field else None
            password = row.get(password_field, "").strip() if password_field else "Student@123"
            room = row.get(room_field, "").strip() if room_field else None

            if not user_id or not name or not email:
                errors.append(f"Row {idx}: Missing mandatory user_id, name, or email.")
                continue

            # Duplicate check in CSV batch
            if user_id in seen_ids:
                duplicates_rejected += 1
                errors.append(f"Row {idx}: Duplicate student ID '{user_id}' within upload file.")
                continue
            seen_ids.add(user_id)

            # Duplicate check in Database
            existing = User.objects(Q(user_id=user_id) | Q(email=email)).first()
            if existing:
                duplicates_rejected += 1
                errors.append(f"Row {idx}: Student ID '{user_id}' or email '{email}' already registered.")
                continue

            student = Student(
                user_id=user_id,
                name=name,
                email=email,
                phone=phone,
                password_hash=hash_password(password),
                role=UserRole.STUDENT.value,
                enrollment_no=user_id,
                hostel_room=room
            )
            student.save()
            imported_count += 1

        audit = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.STUDENT_IMPORTED.value,
            entity_type="SYSTEM",
            details=f"Bulk student CSV imported: {imported_count} saved, {duplicates_rejected} duplicates rejected."
        )
        audit.save()

        return CSVImportResponse(
            total_processed=total_processed,
            successfully_imported=imported_count,
            duplicates_rejected=duplicates_rejected,
            errors=errors[:15],  # Return up to 15 row errors
            message=f"CSV import complete. {imported_count} students added, {duplicates_rejected} duplicates skipped."
        )

    # ------------------ Staff Master Records (F14) ------------------

    @classmethod
    def create_staff(cls, db, admin_user: User, data: StaffCreateRequest) -> StaffRecord:
        """Create a new maintenance/administrative worker record (F14, U8)."""
        staff = StaffRecord(
            name=data.name.strip(),
            contact=data.contact.strip(),
            category_id=data.category_id,
            is_active=data.is_active,
            notes=data.notes.strip() if data.notes else None
        )
        staff.save()

        audit = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.STAFF_CREATED.value,
            entity_type="STAFF",
            details=f"Staff record '{staff.name}' added."
        )
        audit.save()
        return staff

    @classmethod
    def update_staff(cls, db, admin_user: User, staff_id: int, data: StaffUpdateRequest) -> StaffRecord:
        """Update staff member details."""
        staff = StaffRecord.objects(id=staff_id).first()
        if not staff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")

        if data.name is not None:
            staff.name = data.name.strip()
        if data.contact is not None:
            staff.contact = data.contact.strip()
        if data.category_id is not None:
            staff.category_id = data.category_id
        if data.is_active is not None:
            staff.is_active = data.is_active
        if data.notes is not None:
            staff.notes = data.notes.strip()

        staff.save()
        return staff

    # ------------------ Grievance Categories (F14) ------------------

    @classmethod
    def create_category(cls, db, admin_user: User, data: CategoryCreateRequest) -> Category:
        """Add new grievance category (F14, U8)."""
        existing = Category.objects(name__iexact=data.name.strip()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category '{data.name}' already exists.")

        cat = Category(
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            is_active=True
        )
        cat.save()

        audit = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.CATEGORY_CREATED.value,
            entity_type="CATEGORY",
            details=f"Category '{cat.name}' created."
        )
        audit.save()
        return cat

    @classmethod
    def update_category(cls, db, admin_user: User, category_id: int, data: CategoryUpdateRequest) -> Category:
        """Edit category name or description."""
        cat = Category.objects(id=category_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        if data.name is not None:
            cat.name = data.name.strip()
        if data.description is not None:
            cat.description = data.description.strip()
        if data.is_active is not None:
            cat.is_active = data.is_active

        cat.save()

        audit = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.CATEGORY_UPDATED.value,
            entity_type="CATEGORY",
            details=f"Category '{cat.name}' updated."
        )
        audit.save()
        return cat

    @classmethod
    def delete_category(cls, db, admin_user: User, category_id: int) -> Dict[str, str]:
        """
        Delete grievance category (F14, U8).
        Safeguard: A category with open tickets cannot be deleted.
        """
        cat = Category.objects(id=category_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        # Business safeguard enforcement (F14 / U8 Exception)
        can_delete, reason = cat.can_be_deleted()
        if not can_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )

        cat_name = cat.name
        cat.delete()

        audit = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.CATEGORY_DELETED.value,
            entity_type="CATEGORY",
            details=f"Category '{cat_name}' deleted."
        )
        audit.save()
        return {"message": f"Category '{cat_name}' successfully deleted."}

    # ------------------ Audit Logs & Reports (F15, U9) ------------------

    @classmethod
    def get_audit_logs(
        cls,
        db,
        limit: int = 100,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogResponse]:
        """
        Retrieve immutable system audit logs (F15, NFR 4.2).
        Non-editable from the portal.
        """
        query = AuditLog.objects

        if action and action.strip():
            query = query.filter(action=action.strip().upper())
        if start_date:
            query = query.filter(timestamp__gte=start_date)
        if end_date:
            query = query.filter(timestamp__lte=end_date)

        logs = query.order_by("-timestamp").limit(limit)

        result = []
        for l in logs:
            result.append(AuditLogResponse(
                id=l.id,
                user_id=l.user_id,
                user_name=l.user.name if l.user else "System",
                user_role=l.user.role if l.user else "SYSTEM",
                action=l.action,
                entity_type=l.entity_type,
                entity_id=l.entity_id,
                details=l.details,
                ip_address=l.ip_address,
                timestamp=l.timestamp
            ))
        return result

    @classmethod
    def generate_report(
        cls,
        db,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ReportResponse:
        """
        Generate ticket summary report aggregated by category and status (F15, U9).
        """
        query = Ticket.objects
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)

        tickets = list(query)
        categories = list(Category.objects)

        summary_map: Dict[int, Dict[str, Any]] = {
            c.id: {
                "category_id": c.id,
                "category_name": c.name,
                "open_count": 0,
                "in_progress_count": 0,
                "resolved_count": 0,
                "closed_count": 0,
                "duplicate_count": 0,
                "total_count": 0
            } for c in categories
        }

        total_open = 0
        total_in_progress = 0
        total_resolved = 0
        total_closed = 0
        total_duplicate = 0

        for t in tickets:
            item = summary_map.get(t.category_id)
            if item:
                item["total_count"] += 1
                if t.status == TicketStatus.OPEN.value:
                    item["open_count"] += 1
                    total_open += 1
                elif t.status == TicketStatus.IN_PROGRESS.value:
                    item["in_progress_count"] += 1
                    total_in_progress += 1
                elif t.status == TicketStatus.RESOLVED.value:
                    item["resolved_count"] += 1
                    total_resolved += 1
                elif t.status == TicketStatus.CLOSED.value:
                    item["closed_count"] += 1
                    total_closed += 1
                elif t.status == TicketStatus.DUPLICATE.value:
                    item["duplicate_count"] += 1
                    total_duplicate += 1

        summary_list = [ReportSummaryItem(**v) for v in summary_map.values()]

        return ReportResponse(
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
            total_tickets=len(tickets),
            total_open=total_open,
            total_in_progress=total_in_progress,
            total_resolved=total_resolved,
            total_closed=total_closed,
            total_duplicate=total_duplicate,
            summary=summary_list
        )

    @classmethod
    def export_report_csv(
        cls,
        db,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export category and status summary as CSV text (F15)."""
        report = cls.generate_report(db, start_date, end_date)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header section
        writer.writerow(["Campus Grievance Addressal System (CGAS) - Summary Report"])
        writer.writerow(["Generated At", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")])
        writer.writerow(["Start Date", report.start_date or "All History"])
        writer.writerow(["End Date", report.end_date or "Present"])
        writer.writerow([])

        # Table Header
        writer.writerow([
            "Category",
            "OPEN",
            "IN PROGRESS",
            "RESOLVED",
            "CLOSED",
            "DUPLICATE",
            "Total Tickets"
        ])

        for item in report.summary:
            writer.writerow([
                item.category_name,
                item.open_count,
                item.in_progress_count,
                item.resolved_count,
                item.closed_count,
                item.duplicate_count,
                item.total_count
            ])

        writer.writerow([])
        writer.writerow([
            "TOTAL",
            report.total_open,
            report.total_in_progress,
            report.total_resolved,
            report.total_closed,
            report.total_duplicate,
            report.total_tickets
        ])

        return output.getvalue()
