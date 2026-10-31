"""Unit tests for OOP domain models, inheritance, and business policies."""

from datetime import datetime, timedelta, timezone
import pytest
from app.models import (
    User,
    Student,
    Admin,
    Category,
    StaffRecord,
    Ticket,
    TicketLog,
    Feedback,
    Notification,
    PasswordResetOTP,
    UserRole,
    TicketStatus
)

def test_user_inheritance_and_polymorphism(db_session):
    """Verify OOP inheritance of User -> Student and Admin."""
    student = Student(
        user_id="25CSB0A01",
        name="Test Student",
        email="test.student@campus.edu",
        role=UserRole.STUDENT.value,
        enrollment_no="ENROLL001",
        hostel_room="H1-101"
    )
    student.set_password("StudentPass123")

    admin = Admin(
        user_id="admin_test",
        name="Test Admin",
        email="test.admin@campus.edu",
        role=UserRole.ADMIN.value,
        department="Facilities",
        admin_level="SENIOR"
    )
    admin.set_password("AdminPass123")

    db_session.add(student)
    db_session.add(admin)
    db_session.commit()

    # Query polymorphism
    users = db_session.query(User).all()
    assert len(users) == 2

    queried_student = db_session.query(Student).filter_by(user_id="25CSB0A01").first()
    assert queried_student is not None
    assert queried_student.enrollment_no == "ENROLL001"
    assert queried_student.verify_password("StudentPass123") is True
    assert queried_student.verify_password("WrongPass") is False
    assert queried_student.can_view_confidential_tickets() is False

    queried_admin = db_session.query(Admin).filter_by(user_id="admin_test").first()
    assert queried_admin is not None
    assert queried_admin.department == "Facilities"
    assert queried_admin.can_view_confidential_tickets() is True
    assert queried_admin.can_manage_categories() is True


def test_account_lockout_policy(db_session):
    """Verify requirement F2: Lock account for 15 minutes after 5 failed attempts."""
    student = Student(
        user_id="25CSB0A99",
        name="Lockout Test",
        email="lockout@campus.edu",
        role=UserRole.STUDENT.value
    )
    student.set_password("Secret123")
    db_session.add(student)
    db_session.commit()

    assert student.is_locked() is False
    assert student.failed_login_attempts == 0

    # 4 failed attempts should not lock
    for _ in range(4):
        was_locked = student.record_failed_attempt()
        assert was_locked is False
        assert student.is_locked() is False

    # 5th failed attempt triggers lock
    was_locked = student.record_failed_attempt()
    assert was_locked is True
    assert student.is_locked() is True
    assert student.failed_login_attempts == 5
    assert student.locked_until is not None

    # Reset on successful authentication
    student.reset_failed_attempts()
    assert student.is_locked() is False
    assert student.failed_login_attempts == 0


def test_category_deletion_safeguard(db_session):
    """Verify requirement F14: A category with open tickets cannot be deleted."""
    cat = Category(name="Carpentry Test", description="Carpentry maintenance")
    student = Student(user_id="std1", name="S1", email="s1@test.com", role=UserRole.STUDENT.value)
    student.set_password("pass123")
    db_session.add_all([cat, student])
    db_session.commit()

    # With no tickets, can be deleted
    can_delete, msg = cat.can_be_deleted()
    assert can_delete is True

    # Add active open ticket
    ticket = Ticket(
        ticket_id="TKT-TEST-001",
        student_id=student.id,
        category_id=cat.id,
        location="Room 101",
        description="Broken desk leg",
        status=TicketStatus.OPEN.value
    )
    db_session.add(ticket)
    db_session.commit()

    # Now deletion should be blocked
    can_delete, msg = cat.can_be_deleted()
    assert can_delete is False
    assert "active open/in-progress tickets" in msg

    # Resolve ticket
    ticket.status = TicketStatus.RESOLVED.value
    db_session.commit()
    can_delete, msg = cat.can_be_deleted()
    assert can_delete is True


def test_duplicate_linking_and_cascading_close(db_session):
    """Verify requirements F7 and F11: Duplicate ticket linking and cascading closure."""
    cat = Category(name="Plumbing Test")
    student1 = Student(user_id="std2", name="S2", email="s2@test.com", role=UserRole.STUDENT.value)
    student2 = Student(user_id="std3", name="S3", email="s3@test.com", role=UserRole.STUDENT.value)
    student1.set_password("pass123")
    student2.set_password("pass123")
    db_session.add_all([cat, student1, student2])
    db_session.commit()

    # Parent ticket
    parent = Ticket(
        ticket_id="TKT-PARENT-01",
        student_id=student1.id,
        category_id=cat.id,
        location="Block A 2nd Floor Washroom",
        description="Leaking tap in washroom",
        status=TicketStatus.OPEN.value
    )
    db_session.add(parent)
    db_session.commit()

    # Child ticket supported by student 2
    child = Ticket(
        ticket_id="TKT-CHILD-01",
        student_id=student2.id,
        category_id=cat.id,
        location="Block A 2nd Floor Washroom",
        description="Water tap is leaking continuously"
    )
    child.link_to_parent(parent)
    db_session.add(child)
    db_session.commit()

    assert child.status == TicketStatus.DUPLICATE.value
    assert child.parent_ticket_id == parent.id
    assert child.is_duplicate() is True
    assert parent.is_parent() is True
    assert len(parent.duplicate_tickets) == 1

    # Closing parent ticket cascades closure to child duplicate (F11)
    closed_children = parent.cascade_close(closed_by_user_id=1, remark="Tap valve replaced.")
    db_session.commit()

    assert parent.status == TicketStatus.CLOSED.value
    assert child.status == TicketStatus.CLOSED.value
    assert len(closed_children) == 1


def test_seven_day_reopen_policy(db_session):
    """Verify requirement F13: Reopening within 7 days allowed, disallowed after."""
    cat = Category(name="Electrical Test")
    student = Student(user_id="std4", name="S4", email="s4@test.com", role=UserRole.STUDENT.value)
    student.set_password("pass123")
    db_session.add_all([cat, student])
    db_session.commit()

    ticket = Ticket(
        ticket_id="TKT-REOPEN-01",
        student_id=student.id,
        category_id=cat.id,
        location="Lab 3",
        description="Ceiling fan not working",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc) - timedelta(days=3)  # Resolved 3 days ago
    )
    db_session.add(ticket)
    db_session.commit()

    # Day 3: Reopen is allowed
    can_reopen, _ = ticket.can_be_reopened()
    assert can_reopen is True

    # Reopen ticket
    ticket.reopen(reason="Fan is making sparks again.")
    assert ticket.status == TicketStatus.OPEN.value
    assert ticket.resolved_at is None

    # Now set resolved_at to 8 days ago
    ticket.status = TicketStatus.RESOLVED.value
    ticket.resolved_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()

    # Day 8: Reopen is blocked
    can_reopen, error_msg = ticket.can_be_reopened()
    assert can_reopen is False
    assert "Reopen window exceeded" in error_msg

    with pytest.raises(ValueError):
        ticket.reopen(reason="Trying to reopen after 8 days")


def test_feedback_rating_validation(db_session):
    """Verify rating must be between 1 and 5 (F13)."""
    cat = Category(name="Feedback Test")
    student = Student(user_id="std5", name="S5", email="s5@test.com", role=UserRole.STUDENT.value)
    student.set_password("pass123")
    db_session.add_all([cat, student])
    db_session.commit()

    ticket = Ticket(
        ticket_id="TKT-FEEDBACK-01",
        student_id=student.id,
        category_id=cat.id,
        location="Room 302",
        description="Window latch loose",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()

    # Valid rating (5 stars)
    feedback = Feedback(
        ticket_id=ticket.id,
        student_id=student.id,
        rating=5,
        comment="Fast and clean work!"
    )
    db_session.add(feedback)
    db_session.commit()
    assert feedback.id is not None

    # Invalid rating (6 stars) should raise ValueError
    with pytest.raises(ValueError):
        Feedback(
            ticket_id=ticket.id,
            student_id=student.id,
            rating=6,
            comment="Invalid rating"
        )


def test_otp_generation_and_expiry():
    """Verify OTP 5-minute single-use validity (F3, NFR 4.2)."""
    now = datetime.now(timezone.utc)
    valid_otp = PasswordResetOTP(
        user_id=1,
        otp_code="123456",
        expires_at=now + timedelta(minutes=5),
        is_used=False
    )
    assert valid_otp.is_valid("123456") is True
    assert valid_otp.is_valid("999999") is False  # Wrong code

    # Test single-use invalidation
    valid_otp.mark_used()
    assert valid_otp.is_valid("123456") is False

    # Test expiration
    expired_otp = PasswordResetOTP(
        user_id=1,
        otp_code="654321",
        expires_at=now - timedelta(seconds=1),
        is_used=False
    )
    assert expired_otp.is_valid("654321") is False
