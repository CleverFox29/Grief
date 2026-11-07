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

def test_serviceman_active_tickets_count(client, student_auth_header, admin_auth_header, db_session):
    """Test that active_tickets_count accurately reflects open/in-progress issues assigned to a serviceman."""
    carp_cat = Category.objects(name="Carpentry").first()
    if not carp_cat:
        carp_cat = Category(name="Carpentry", description="Woodwork repairs").save()

    serviceman = Serviceman(
        user_id="service_count_test",
        name="Counter Worker",
        email="count@campus.edu",
        category="Carpentry",
        phone="+91-9876543299",
        password_hash=hash_password("Pass1234")
    )
    serviceman.save()

    # Query servicemen list: count should initially be 0
    resp = client.get("/api/servicemen?category=Carpentry", headers=admin_auth_header)
    assert resp.status_code == 200
    sm_data = next((s for s in resp.json() if s["id"] == serviceman.id), None)
    assert sm_data is not None
    assert sm_data["active_tickets_count"] == 0

    # Student creates ticket
    create_resp = client.post(
        "/api/tickets",
        data={
            "category_id": carp_cat.id,
            "location": "Hostel 3, Room 101",
            "description": "Desk leg cracked and needs support.",
            "is_confidential": False,
            "action": "CREATE"
        },
        headers=student_auth_header
    )
    t_id = create_resp.json()["id"]

    # Admin assigns ticket to this serviceman
    client.patch(
        f"/api/tickets/{t_id}",
        json={
            "assigned_serviceman_id": serviceman.id,
            "remark": "Assigned to Counter Worker"
        },
        headers=admin_auth_header
    )

    # Active count should now be 1
    resp2 = client.get("/api/servicemen?category=Carpentry", headers=admin_auth_header)
    sm_data2 = next((s for s in resp2.json() if s["id"] == serviceman.id), None)
    assert sm_data2["active_tickets_count"] == 1

def test_serviceman_cannot_resolve_unless_in_progress(client, student_auth_header, admin_auth_header, db_session):
    """Verify that serviceman can only transition from IN PROGRESS to RESOLVED (pending confirmation)."""
    carp_cat = Category.objects(name="Carpentry").first()
    if not carp_cat:
        carp_cat = Category(name="Carpentry", description="Woodwork repairs").save()

    serviceman = Serviceman(
        user_id="service_strict_test",
        name="Strict Worker",
        email="strict@campus.edu",
        category="Carpentry",
        password_hash=hash_password("Pass1234")
    )
    serviceman.save()

    # Student creates ticket
    create_resp = client.post(
        "/api/tickets",
        data={
            "category_id": carp_cat.id,
            "location": "Room 50",
            "description": "Broken hinge on closet door",
            "is_confidential": False,
            "action": "CREATE"
        },
        headers=student_auth_header
    )
    t_id = create_resp.json()["id"]

    # Directly set assigned serviceman but keep status OPEN
    ticket = Ticket.objects(id=t_id).first()
    ticket.assigned_serviceman_id = serviceman.id
    ticket.status = TicketStatus.OPEN.value
    ticket.save()

    sm_login = client.post("/api/auth/login", json={
        "role": "SERVICEMAN",
        "user_id": "service_strict_test",
        "password": "Pass1234"
    })
    sm_auth = {"Authorization": f"Bearer {sm_login.json()['access_token']}"}

    # Attempt to resolve while OPEN: must fail with 400
    resolve_resp = client.post(
        f"/api/tickets/{t_id}/resolve",
        json={"serviceman_remark": "Attempting early resolution without starting work."},
        headers=sm_auth
    )
    assert resolve_resp.status_code == 400
    assert "IN PROGRESS" in resolve_resp.json()["detail"]

    # Now schedule visit or set to IN PROGRESS
    ticket.status = TicketStatus.IN_PROGRESS.value
    ticket.save()

    # Attempt to resolve while IN PROGRESS: must succeed
    resolve_ok = client.post(
        f"/api/tickets/{t_id}/resolve",
        json={"serviceman_remark": "Hinge replaced and tested."},
        headers=sm_auth
    )
    assert resolve_ok.status_code == 200
    assert resolve_ok.json()["status"] == "PENDING CONFIRMATION"

def test_admin_servicemen_csv_and_manual_creation(client, admin_auth_header, db_session):
    """Test Admin manual addition and CSV bulk import for Servicemen accounts."""
    admin_cat = Category(name="Administrative", description="Admin services").save()

    # 1. Manual creation
    manual_resp = client.post(
        "/api/admin/servicemen",
        json={
            "user_id": "service_anita_test",
            "name": "Anita Desai",
            "email": "anita.desai@campus.edu",
            "category": "Administrative",
            "phone": "+91-9876543205",
            "password": "Serviceman@123"
        },
        headers=admin_auth_header
    )
    assert manual_resp.status_code == 201
    manual_data = manual_resp.json()
    assert manual_data["user_id"] == "service_anita_test"
    assert manual_data["category"] == "Administrative"

    # Verify duplicate rejection
    dup_resp = client.post(
        "/api/admin/servicemen",
        json={
            "user_id": "service_anita_test",
            "name": "Duplicate Anita",
            "email": "another@campus.edu",
            "category": "Administrative"
        },
        headers=admin_auth_header
    )
    assert dup_resp.status_code == 400

    # 2. Bulk CSV import
    csv_content = (
        "user_id,name,email,category,phone\n"
        "service_vikram_test,Vikram Singh,vikram.test@campus.edu,Masonry,+91-9876543204\n"
        "service_devendra_test,Devendra Pal,devendra.test@campus.edu,Security,+91-9876543206\n"
        "service_anita_test,Duplicate Anita,anita.dup@campus.edu,Administrative,+91-0000000000\n"
    ).encode("utf-8")

    import_resp = client.post(
        "/api/admin/servicemen/import-csv",
        files={"file": ("servicemen.csv", csv_content, "text/csv")},
        headers=admin_auth_header
    )
    assert import_resp.status_code == 200
    res_data = import_resp.json()
    assert res_data["total_processed"] == 3
    assert res_data["successfully_imported"] == 2
    assert res_data["duplicates_rejected"] == 1

    # Verify newly imported serviceman can log in
    sm_login = client.post("/api/auth/login", json={
        "role": "SERVICEMAN",
        "user_id": "service_vikram_test",
        "password": "Serviceman@123"
    })
    assert sm_login.status_code == 200
    assert sm_login.json()["user"]["name"] == "Vikram Singh"
