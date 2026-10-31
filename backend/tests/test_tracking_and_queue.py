"""Integration tests for Phase 4: Ticket Tracking, Queue Management, Admin Triage, and Cascading Close (F8-F12)."""

from datetime import datetime, timezone
import pytest
from app.models import Category, StaffRecord, Student, Admin, Ticket, TicketStatus, UserRole

@pytest.fixture
def phase4_setup(client, db_session):
    """Seed categories, staff, student, and admin for Phase 4 tests."""
    # 1. Categories
    cat_plumbing = Category(name="Plumbing", description="Plumbing")
    cat_elec = Category(name="Electrical", description="Electrical")
    db_session.add_all([cat_plumbing, cat_elec])
    db_session.flush()

    # 2. Staff
    staff1 = StaffRecord(name="Ramesh (Plumber)", contact="+91-9876543201", category_id=cat_plumbing.id)
    staff2 = StaffRecord(name="Suresh (Electrician)", contact="+91-9876543202", category_id=cat_elec.id)
    db_session.add_all([staff1, staff2])
    db_session.flush()

    # 3. Student 1
    s1 = Student(user_id="std1", name="Student One", email="s1@test.com", role=UserRole.STUDENT.value)
    s1.set_password("Pass123")
    
    # 4. Student 2
    s2 = Student(user_id="std2", name="Student Two", email="s2@test.com", role=UserRole.STUDENT.value)
    s2.set_password("Pass123")

    # 5. Admin
    admin = Admin(user_id="admin01", name="Head Admin", email="admin@test.com", role=UserRole.ADMIN.value, department="Facilities")
    admin.set_password("Admin123")

    db_session.add_all([s1, s2, admin])
    db_session.commit()

    # Get student token
    s1_login = client.post("/api/auth/login", json={"user_id": "std1", "password": "Pass123", "role": "STUDENT"})
    s1_token = s1_login.json()["access_token"]

    # Get admin token
    admin_login = client.post("/api/auth/login", json={"user_id": "admin01", "password": "Admin123", "role": "ADMIN"})
    admin_token = admin_login.json()["access_token"]

    return {
        "cat_plumbing": cat_plumbing,
        "cat_elec": cat_elec,
        "staff_plumber": staff1,
        "s1": s1,
        "s2": s2,
        "admin": admin,
        "s1_header": {"Authorization": f"Bearer {s1_token}"},
        "admin_header": {"Authorization": f"Bearer {admin_token}"}
    }

def test_student_track_my_tickets(client, db_session, phase4_setup):
    """F8, U4: Student views their own tickets sorted newest first."""
    s1 = phase4_setup["s1"]
    cat = phase4_setup["cat_plumbing"]
    header = phase4_setup["s1_header"]

    t1 = Ticket(ticket_id="TKT-01", student_id=s1.id, category_id=cat.id, location="Room 101", description="Leak 1")
    t2 = Ticket(ticket_id="TKT-02", student_id=s1.id, category_id=cat.id, location="Room 102", description="Leak 2")
    db_session.add_all([t1, t2])
    db_session.commit()

    response = client.get("/api/tickets/my-tickets", headers=header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["ticket_id"] == "TKT-02"  # Newest first

def test_admin_unified_queue_search_and_filter(client, db_session, phase4_setup):
    """F9, F10, U5: Admin searches by ID and filters by category/status."""
    s1 = phase4_setup["s1"]
    cat_p = phase4_setup["cat_plumbing"]
    cat_e = phase4_setup["cat_elec"]
    header = phase4_setup["admin_header"]

    t1 = Ticket(ticket_id="TKT-2026-0001", student_id=s1.id, category_id=cat_p.id, location="H1 Room 1", description="Pipe issue", status="OPEN")
    t2 = Ticket(ticket_id="TKT-2026-0002", student_id=s1.id, category_id=cat_e.id, location="H2 Room 2", description="Bulb issue", status="IN PROGRESS")
    db_session.add_all([t1, t2])
    db_session.commit()

    # Search by Ticket ID
    search_resp = client.get("/api/tickets/admin-queue?search=0002", headers=header)
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert len(data) == 1
    assert data[0]["ticket_id"] == "TKT-2026-0002"

    # Filter by category
    filter_resp = client.get(f"/api/tickets/admin-queue?category_id={cat_p.id}", headers=header)
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 1
    assert filter_resp.json()[0]["category_name"] == "Plumbing"

def test_duplicate_tickets_grouped_under_parent(client, db_session, phase4_setup):
    """U5 Notes: Duplicate tickets are shown grouped under their parent ticket."""
    s1 = phase4_setup["s1"]
    s2 = phase4_setup["s2"]
    cat = phase4_setup["cat_plumbing"]
    header = phase4_setup["admin_header"]

    parent = Ticket(ticket_id="TKT-PARENT", student_id=s1.id, category_id=cat.id, location="H1 Bath", description="Drain clogged")
    db_session.add(parent)
    db_session.commit()

    child = Ticket(ticket_id="TKT-CHILD", student_id=s2.id, category_id=cat.id, location="H1 Bath", description="Water backed up")
    child.link_to_parent(parent)
    db_session.add(child)
    db_session.commit()

    # Admin queue should list parent ticket with child nested
    queue_resp = client.get("/api/tickets/admin-queue", headers=header)
    assert queue_resp.status_code == 200
    data = queue_resp.json()
    
    parent_item = next(item for item in data if item["ticket_id"] == "TKT-PARENT")
    assert parent_item["duplicate_count"] == 1
    assert len(parent_item["duplicate_children"]) == 1
    assert parent_item["duplicate_children"][0]["ticket_id"] == "TKT-CHILD"

def test_admin_update_assign_staff_and_cascading_closure(client, db_session, phase4_setup):
    """F11, F12, U6: Assign staff, update status, and cascade close to linked duplicates."""
    s1 = phase4_setup["s1"]
    s2 = phase4_setup["s2"]
    cat = phase4_setup["cat_plumbing"]
    staff = phase4_setup["staff_plumber"]
    admin_header = phase4_setup["admin_header"]
    student_header = phase4_setup["s1_header"]

    parent = Ticket(ticket_id="TKT-P1", student_id=s1.id, category_id=cat.id, location="Washroom", description="Leak")
    db_session.add(parent)
    db_session.commit()

    child = Ticket(ticket_id="TKT-C1", student_id=s2.id, category_id=cat.id, location="Washroom", description="Leak")
    child.link_to_parent(parent)
    db_session.add(child)
    db_session.commit()

    # Step 1: Assign staff and move to IN PROGRESS
    update1 = client.patch(
        f"/api/tickets/{parent.id}",
        headers=admin_header,
        json={
            "status": "IN PROGRESS",
            "assigned_staff_id": staff.id,
            "remark": "Staff assigned to inspect."
        }
    )
    assert update1.status_code == 200
    data1 = update1.json()
    assert data1["status"] == "IN PROGRESS"
    assert data1["assigned_staff_name"] == staff.name

    # Step 2: Close parent ticket -> cascades close to child duplicate (F11)
    update2 = client.patch(
        f"/api/tickets/{parent.id}",
        headers=admin_header,
        json={
            "status": "CLOSED",
            "remark": "Fixed pipe and verified no leakage."
        }
    )
    assert update2.status_code == 200
    data2 = update2.json()
    assert data2["status"] == "CLOSED"

    # Verify child duplicate is now CLOSED in database
    db_session.refresh(child)
    assert child.status == "CLOSED"

    # Step 3: Check student received notification (F12)
    notif_resp = client.get("/api/notifications", headers=student_header)
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert len(notifs) >= 2  # Creation + update notifications
    assert "CLOSED" in notifs[0]["message"]
