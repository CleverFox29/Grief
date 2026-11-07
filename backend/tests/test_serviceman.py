"""Unit and integration tests for Serviceman role, queue, proof submission, and student confirmation."""

import pytest
from app.models import Category, Ticket, TicketStatus, UserRole, Serviceman, Student
from app.core.security import hash_password

def test_serviceman_inheritance_and_properties(db_session):
    """Verify OOP inheritance of User -> Serviceman and trade validation."""
    serviceman = Serviceman(
        user_id="service_test",
        name="Ramesh Carpenter",
        email="ramesh@campus.edu",
        category="Carpentry",
        phone="+91-9876543299",
        password_hash=hash_password("Pass1234")
    )
    db_session.add(serviceman)
    db_session.commit()

    assert serviceman.role == UserRole.SERVICEMAN.value
    assert serviceman.category == "Carpentry"
    assert serviceman.phone_number == "+91-9876543299"
    assert serviceman.verify_password("Pass1234") is True
    assert serviceman.can_view_confidential_tickets() is False

def test_serviceman_ticket_workflow(client, student_auth_header, admin_auth_header, db_session):
    """
    Full end-to-end maintenance workflow:
    1. Student creates grievance in Carpentry.
    2. Serviceman logs in and sees ticket in serviceman queue.
    3. Serviceman claims the ticket (status -> IN PROGRESS).
    4. Serviceman resolves with proof of work and remark (status -> PENDING CONFIRMATION).
    5. Student confirms resolution with 5-star rating (status -> RESOLVED).
    """
    # 1. Ensure category and serviceman exist
    carp_cat = Category.objects(name="Carpentry").first()
    if not carp_cat:
        carp_cat = Category(name="Carpentry", description="Woodwork repairs")
        carp_cat.save()

    serviceman = Serviceman.objects(user_id="service_carpenter_test").first()
    if not serviceman:
        serviceman = Serviceman(
            user_id="service_carpenter_test",
            name="Manoj Sharma",
            email="manoj.test@campus.edu",
            category="Carpentry",
            phone="+91-9876543202",
            password_hash=hash_password("Serviceman@123")
        )
        serviceman.save()

    # Serviceman Login
    sm_login_resp = client.post("/api/auth/login", json={
        "role": "SERVICEMAN",
        "user_id": "service_carpenter_test",
        "password": "Serviceman@123"
    })
    assert sm_login_resp.status_code == 200
    sm_data = sm_login_resp.json()
    assert sm_data["user"]["role"] == "SERVICEMAN"
    assert sm_data["user"]["category"] == "Carpentry"
    sm_token = sm_data["access_token"]
    sm_auth_header = {"Authorization": f"Bearer {sm_token}"}

    # Student creates ticket
    create_resp = client.post(
        "/api/tickets",
        data={
            "category_id": carp_cat.id,
            "location": "Hostel 3, Room 204",
            "description": "Broken study table leg needs urgent carpentry repair.",
            "is_confidential": False,
            "action": "CREATE"
        },
        headers=student_auth_header
    )
    assert create_resp.status_code == 201
    ticket_data = create_resp.json()
    ticket_id = ticket_data["id"]
    assert ticket_data["status"] == "OPEN"

    # Serviceman checks queue
    queue_resp = client.get("/api/tickets/serviceman-queue", headers=sm_auth_header)
    assert queue_resp.status_code == 200
    queue = queue_resp.json()
    matching_tickets = [t for t in queue if t["id"] == ticket_id]
    assert len(matching_tickets) == 1
    assert matching_tickets[0]["category_name"] == "Carpentry"

    # Serviceman claims ticket
    claim_resp = client.post(f"/api/tickets/{ticket_id}/claim", headers=sm_auth_header)
    assert claim_resp.status_code == 200
    assert claim_resp.json()["status"] == "IN PROGRESS"
    assert claim_resp.json()["assigned_serviceman_id"] == serviceman.id

    # Serviceman resolves ticket with proof
    resolve_resp = client.post(
        f"/api/tickets/{ticket_id}/resolve",
        json={
            "serviceman_remark": "Fixed the table leg with new wooden joint and reinforcement screws.",
            "proof_of_work_url": "https://example.com/proof.jpg"
        },
        headers=sm_auth_header
    )
    assert resolve_resp.status_code == 200
    resolved_ticket = resolve_resp.json()
    assert resolved_ticket["status"] == "PENDING CONFIRMATION"
    assert resolved_ticket["proof_of_work_url"] == "https://example.com/proof.jpg"
    assert "reinforcement screws" in resolved_ticket["serviceman_remark"]

    # Student confirms resolution
    confirm_resp = client.post(
        f"/api/tickets/{ticket_id}/confirm",
        json={
            "is_fixed": True,
            "rating": 5,
            "feedback": "Excellent carpentry work, table is completely stable now!"
        },
        headers=student_auth_header
    )
    assert confirm_resp.status_code == 200
    confirmed_ticket = confirm_resp.json()
    assert confirmed_ticket["status"] == "RESOLVED"
    assert confirmed_ticket["student_rating"] == 5
    assert "completely stable" in confirmed_ticket["student_feedback"]

def test_student_reject_fix_workflow(client, student_auth_header, db_session):
    """Verify that student can reject a fix and ticket returns to OPEN status."""
    carp_cat = Category.objects(name="Carpentry").first()
    if not carp_cat:
        carp_cat = Category(name="Carpentry", description="Woodwork repairs")
        carp_cat.save()

    serviceman = Serviceman.objects(user_id="service_carpenter_test").first()
    if not serviceman:
        serviceman = Serviceman(
            user_id="service_carpenter_test",
            name="Manoj Sharma",
            email="manoj.test2@campus.edu",
            category="Carpentry",
            phone="+91-9876543202",
            password_hash=hash_password("Serviceman@123")
        )
        serviceman.save()

    sm_login_resp = client.post("/api/auth/login", json={
        "role": "SERVICEMAN",
        "user_id": "service_carpenter_test",
        "password": "Serviceman@123"
    })
    sm_token = sm_login_resp.json()["access_token"]
    sm_auth_header = {"Authorization": f"Bearer {sm_token}"}

    # Student creates ticket
    create_resp = client.post(
        "/api/tickets",
        data={
            "category_id": carp_cat.id,
            "location": "Hostel 3, Room 101",
            "description": "Wardrobe door latch broken.",
            "is_confidential": False,
            "action": "CREATE"
        },
        headers=student_auth_header
    )
    ticket_id = create_resp.json()["id"]

    # Serviceman claims and resolves
    client.post(f"/api/tickets/{ticket_id}/claim", headers=sm_auth_header)
    client.post(
        f"/api/tickets/{ticket_id}/resolve",
        json={"serviceman_remark": "Adjusted the latch alignment."},
        headers=sm_auth_header
    )

    # Student rejects resolution
    confirm_resp = client.post(
        f"/api/tickets/{ticket_id}/confirm",
        json={
            "is_fixed": False,
            "feedback": "The latch is still loose and door does not shut."
        },
        headers=student_auth_header
    )
    assert confirm_resp.status_code == 200
    rejected_ticket = confirm_resp.json()
    assert rejected_ticket["status"] == "OPEN"
    assert "still loose" in rejected_ticket["student_feedback"]
