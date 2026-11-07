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

    # Serviceman checks queue before admin assignment: issue must NOT be visible
    queue_resp = client.get("/api/tickets/serviceman-queue", headers=sm_auth_header)
    assert queue_resp.status_code == 200
    queue = queue_resp.json()
    matching_tickets = [t for t in queue if t["id"] == ticket_id]
    assert len(matching_tickets) == 0  # Hidden from serviceman until assigned by Admin!

    # Serviceman cannot view ticket details before being assigned
    detail_resp = client.get(f"/api/tickets/{ticket_id}", headers=sm_auth_header)
    assert detail_resp.status_code == 403

    # Admin triages and assigns the ticket to this serviceman
    assign_resp = client.patch(
        f"/api/tickets/{ticket_id}",
        json={
            "assigned_serviceman_id": serviceman.id,
            "remark": "Assigned to Manoj Sharma (Carpentry)"
        },
        headers=admin_auth_header
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["status"] == "IN PROGRESS"

    # Now the issue IS visible to the assigned serviceman in their queue
    queue_after_assign = client.get("/api/tickets/serviceman-queue", headers=sm_auth_header).json()
    matching_after = [t for t in queue_after_assign if t["id"] == ticket_id]
    assert len(matching_after) == 1
    assert matching_after[0]["category_name"] == "Carpentry"
    assert matching_after[0]["assigned_serviceman_id"] == serviceman.id

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

def test_student_reject_fix_workflow(client, student_auth_header, admin_auth_header, db_session):
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

    # Admin assigns serviceman to this ticket so it becomes visible
    client.patch(
        f"/api/tickets/{ticket_id}",
        json={
            "assigned_serviceman_id": serviceman.id,
            "remark": "Assigned to Manoj"
        },
        headers=admin_auth_header
    )

    # Serviceman resolves
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

def test_admin_assign_serviceman_and_schedule_visit(client, student_auth_header, admin_auth_header, db_session):
    """
    Test Admin category-based serviceman query, assignment, and serviceman scheduling visit:
    1. Query /api/servicemen?category=Carpentry
    2. Admin assigns serviceman to an open ticket.
    3. Serviceman schedules visit with remark ('I will visit on Monday at 3 PM').
    """
    carp_cat = Category.objects(name="Carpentry").first()
    if not carp_cat:
        carp_cat = Category(name="Carpentry", description="Woodwork repairs").save()

    serviceman = Serviceman.objects(user_id="service_carpenter_test").first()
    if not serviceman:
        serviceman = Serviceman(
            user_id="service_carpenter_test",
            name="Manoj Sharma",
            email="manoj.test3@campus.edu",
            category="Carpentry",
            phone="+91-9876543202",
            password_hash=hash_password("Serviceman@123")
        ).save()

    # 1. Query servicemen by category
    sm_list_resp = client.get("/api/servicemen?category=Carpentry", headers=admin_auth_header)
    assert sm_list_resp.status_code == 200
    sm_list = sm_list_resp.json()
    assert any(s["id"] == serviceman.id for s in sm_list)

    # 2. Student raises ticket
    create_resp = client.post(
        "/api/tickets",
        data={
            "category_id": carp_cat.id,
            "location": "Hostel 1, Room 10",
            "description": "Chair leg broken",
            "is_confidential": False,
            "action": "CREATE"
        },
        headers=student_auth_header
    )
    assert create_resp.status_code == 201
    ticket_id = create_resp.json()["id"]

    # 3. Admin assigns serviceman
    patch_resp = client.patch(
        f"/api/tickets/{ticket_id}",
        json={
            "assigned_serviceman_id": serviceman.id,
            "remark": "Assigned to Manoj Carpenter"
        },
        headers=admin_auth_header
    )
    assert patch_resp.status_code == 200
    ticket_data = patch_resp.json()
    assert ticket_data["assigned_serviceman_id"] == serviceman.id
    assert ticket_data["status"] == "IN PROGRESS"

    # 4. Serviceman schedules visit
    sm_login = client.post("/api/auth/login", json={
        "role": "SERVICEMAN",
        "user_id": "service_carpenter_test",
        "password": "Serviceman@123"
    })
    sm_auth = {"Authorization": f"Bearer {sm_login.json()['access_token']}"}

    sched_resp = client.post(
        f"/api/tickets/{ticket_id}/schedule",
        json={"scheduling_remark": "I will come on Monday at 3 PM"},
        headers=sm_auth
    )
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert sched_data["scheduling_remark"] == "I will come on Monday at 3 PM"
    assert sched_data["scheduled_at"] is not None

def test_admin_manual_close_workflow(client, student_auth_header, admin_auth_header, db_session):
    """Test Admin manual closure of a ticket at any lifecycle stage."""
    cat = Category.objects.first()
    if not cat:
        cat = Category(name="General", description="General issues").save()

    create_resp = client.post(
        "/api/tickets",
        data={
            "category_id": cat.id,
            "location": "Library 2nd Floor",
            "description": "Old books damaged beyond repair",
            "is_confidential": False,
            "action": "CREATE"
        },
        headers=student_auth_header
    )
    ticket_id = create_resp.json()["id"]

    close_resp = client.post(
        f"/api/tickets/{ticket_id}/close",
        json={"remark": "Books replaced, old records written off manually."},
        headers=admin_auth_header
    )
    assert close_resp.status_code == 200
    closed_data = close_resp.json()
    assert closed_data["status"] == "CLOSED"
    assert closed_data["closed_at"] is not None
