"""Integration tests for Phase 5: Feedback Rating and 7-Day Reopen Loop (F13, U7)."""

from datetime import datetime, timedelta, timezone
import pytest
from app.models import Category, Student, Ticket, TicketStatus, UserRole

@pytest.fixture
def feedback_setup(client, db_session):
    """Seed category, students, and tokens for Phase 5 testing."""
    cat = Category(name="Carpentry", description="Carpentry")
    s1 = Student(user_id="std1", name="Student One", email="s1@test.com", role=UserRole.STUDENT.value)
    s1.set_password("Pass123")
    s2 = Student(user_id="std2", name="Student Two", email="s2@test.com", role=UserRole.STUDENT.value)
    s2.set_password("Pass123")

    db_session.add_all([cat, s1, s2])
    db_session.commit()

    s1_login = client.post("/api/auth/login", json={"user_id": "std1", "password": "Pass123", "role": "STUDENT"})
    s1_token = s1_login.json()["access_token"]

    s2_login = client.post("/api/auth/login", json={"user_id": "std2", "password": "Pass123", "role": "STUDENT"})
    s2_token = s2_login.json()["access_token"]

    return {
        "cat": cat,
        "s1": s1,
        "s2": s2,
        "s1_header": {"Authorization": f"Bearer {s1_token}"},
        "s2_header": {"Authorization": f"Bearer {s2_token}"}
    }

def test_submit_feedback_on_resolved_ticket(client, db_session, feedback_setup):
    """F13, U7: Student submits 1-5 rating and comment on a RESOLVED ticket."""
    s1 = feedback_setup["s1"]
    cat = feedback_setup["cat"]
    header = feedback_setup["s1_header"]

    ticket = Ticket(
        ticket_id="TKT-RES-01",
        student_id=s1.id,
        category_id=cat.id,
        location="Hostel 1",
        description="Bed frame loose",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()

    # Submit 5-star rating with comment
    response = client.post(
        f"/api/tickets/{ticket.id}/feedback",
        headers=header,
        json={"rating": 5, "comment": "Carpenter was prompt and polite."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5
    assert data["comment"] == "Carpenter was prompt and polite."
    assert data["ticket_id"] == ticket.id

def test_feedback_rating_boundary_validation(client, db_session, feedback_setup):
    """F13: Rating must be within 1 to 5 stars."""
    s1 = feedback_setup["s1"]
    cat = feedback_setup["cat"]
    header = feedback_setup["s1_header"]

    ticket = Ticket(
        ticket_id="TKT-RES-02",
        student_id=s1.id,
        category_id=cat.id,
        location="Hostel 1",
        description="Bed frame loose",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()

    # 6 stars is invalid
    bad_resp = client.post(
        f"/api/tickets/{ticket.id}/feedback",
        headers=header,
        json={"rating": 6, "comment": "Too high"}
    )
    assert bad_resp.status_code == 422

    # 0 stars is invalid
    bad_resp2 = client.post(
        f"/api/tickets/{ticket.id}/feedback",
        headers=header,
        json={"rating": 0, "comment": "Too low"}
    )
    assert bad_resp2.status_code == 422

def test_reopen_ticket_within_seven_days(client, db_session, feedback_setup):
    """F13, U7: Student reopens ticket within 7 days -> returns to OPEN with note."""
    s1 = feedback_setup["s1"]
    cat = feedback_setup["cat"]
    header = feedback_setup["s1_header"]

    ticket = Ticket(
        ticket_id="TKT-REOPEN-TEST",
        student_id=s1.id,
        category_id=cat.id,
        location="Hostel 2, Room 10",
        description="Door lock jamming",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc) - timedelta(days=2)  # Resolved 2 days ago
    )
    db_session.add(ticket)
    db_session.commit()

    response = client.post(
        f"/api/tickets/{ticket.id}/reopen",
        headers=header,
        json={"reason": "Lock is sticking again after 2 days."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPEN"
    assert data["resolved_at"] is None

    # Verify timeline log contains reopening remark
    latest_log = data["logs"][0]
    assert latest_log["action"] == "TICKET_REOPENED"
    assert "Lock is sticking again" in latest_log["remark"]

def test_reopen_ticket_blocked_after_seven_days(client, db_session, feedback_setup):
    """F13, U7 Exception: More than 7 days have passed -> reopen is blocked."""
    s1 = feedback_setup["s1"]
    cat = feedback_setup["cat"]
    header = feedback_setup["s1_header"]

    ticket = Ticket(
        ticket_id="TKT-EXPIRED-TEST",
        student_id=s1.id,
        category_id=cat.id,
        location="Hostel 2, Room 10",
        description="Door lock jamming",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc) - timedelta(days=8)  # Resolved 8 days ago
    )
    db_session.add(ticket)
    db_session.commit()

    response = client.post(
        f"/api/tickets/{ticket.id}/reopen",
        headers=header,
        json={"reason": "Trying to reopen after 8 days."}
    )
    assert response.status_code == 400
    assert "Reopen window exceeded" in response.json()["detail"]
    assert "raise a new ticket" in response.json()["detail"]

def test_cannot_reopen_or_review_other_student_ticket(client, db_session, feedback_setup):
    """NFR 4.2: Student cannot review or reopen tickets belonging to peers."""
    s1 = feedback_setup["s1"]
    cat = feedback_setup["cat"]
    s2_header = feedback_setup["s2_header"]

    ticket = Ticket(
        ticket_id="TKT-S1-ONLY",
        student_id=s1.id,
        category_id=cat.id,
        location="Hostel 1",
        description="Desk cracked",
        status=TicketStatus.RESOLVED.value,
        resolved_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()

    # Student 2 tries to review Student 1's ticket
    feedback_resp = client.post(
        f"/api/tickets/{ticket.id}/feedback",
        headers=s2_header,
        json={"rating": 5}
    )
    assert feedback_resp.status_code == 403

    # Student 2 tries to reopen Student 1's ticket
    reopen_resp = client.post(
        f"/api/tickets/{ticket.id}/reopen",
        headers=s2_header,
        json={"reason": "Unauthorized reopen"}
    )
    assert reopen_resp.status_code == 403
