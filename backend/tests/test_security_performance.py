"""Security hardening and performance benchmark tests (NFR 4.1, 4.2)."""

import time
import pytest
from app.models import Category, Student, Admin, Ticket, TicketStatus, UserRole
from app.services.deduplication_service import DeduplicationEngine

@pytest.fixture
def sec_setup(client, db_session):
    """Seed student, admin, and category."""
    cat = Category(name="Security & Safety")
    s1 = Student(user_id="student_sec1", name="Alice", email="alice@test.com", role=UserRole.STUDENT.value)
    s1.set_password("SecurePass@123")
    s2 = Student(user_id="student_sec2", name="Bob", email="bob@test.com", role=UserRole.STUDENT.value)
    s2.set_password("SecurePass@123")
    admin = Admin(user_id="admin_sec", name="Security Admin", email="adminsec@test.com", role=UserRole.ADMIN.value)
    admin.set_password("AdminPass@123")

    db_session.add_all([cat, s1, s2, admin])
    db_session.commit()

    s1_login = client.post("/api/auth/login", json={"user_id": "student_sec1", "password": "SecurePass@123", "role": "STUDENT"})
    s1_token = s1_login.json()["access_token"]

    s2_login = client.post("/api/auth/login", json={"user_id": "student_sec2", "password": "SecurePass@123", "role": "STUDENT"})
    s2_token = s2_login.json()["access_token"]

    admin_login = client.post("/api/auth/login", json={"user_id": "admin_sec", "password": "AdminPass@123", "role": "ADMIN"})
    admin_token = admin_login.json()["access_token"]

    return {
        "cat": cat,
        "s1": s1,
        "s2": s2,
        "admin": admin,
        "s1_header": {"Authorization": f"Bearer {s1_token}"},
        "s2_header": {"Authorization": f"Bearer {s2_token}"},
        "admin_header": {"Authorization": f"Bearer {admin_token}"}
    }

def test_sql_injection_defense_in_search(client, sec_setup, db_session):
    """NFR 4.2: Parameterized query defense against SQL Injection."""
    cat = sec_setup["cat"]
    s1 = sec_setup["s1"]
    admin_header = sec_setup["admin_header"]

    t = Ticket(
        ticket_id="TKT-SEC-01",
        student_id=s1.id,
        category_id=cat.id,
        location="Main Gate",
        description="Gate lock loose"
    )
    db_session.add(t)
    db_session.commit()

    # Classic SQLi payloads
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE tickets; --",
        "' UNION SELECT * FROM users --",
        "1; WAITFOR DELAY '0:0:5'--"
    ]

    for payload in sqli_payloads:
        resp = client.get(f"/api/tickets/admin-queue?search={payload}", headers=admin_header)
        assert resp.status_code == 200
        # Database table remains fully intact
        assert db_session.query(Ticket).count() >= 1

def test_confidential_grievance_strict_isolation(client, sec_setup, db_session):
    """F4, NFR 4.2: Confidential ticket is strictly isolated from non-author students."""
    cat = sec_setup["cat"]
    s1 = sec_setup["s1"]
    s1_header = sec_setup["s1_header"]
    s2_header = sec_setup["s2_header"]
    admin_header = sec_setup["admin_header"]

    conf_ticket = Ticket(
        ticket_id="TKT-CONF-01",
        student_id=s1.id,
        category_id=cat.id,
        location="Hostel 3 Common Room",
        description="Harassment report containing sensitive student names",
        is_confidential=True
    )
    db_session.add(conf_ticket)
    db_session.commit()

    # Author student can view their own confidential ticket
    author_resp = client.get(f"/api/tickets/{conf_ticket.id}", headers=s1_header)
    assert author_resp.status_code == 200

    # Peer student Bob is strictly blocked (HTTP 403 Forbidden)
    peer_resp = client.get(f"/api/tickets/{conf_ticket.id}", headers=s2_header)
    assert peer_resp.status_code == 403
    assert "Access denied" in peer_resp.json()["detail"] or "confidential" in peer_resp.json()["detail"]

    # Admin can view confidential grievance
    admin_resp = client.get(f"/api/tickets/{conf_ticket.id}", headers=admin_header)
    assert admin_resp.status_code == 200
    assert admin_resp.json()["is_confidential"] is True

def test_deduplication_performance_benchmark(db_session, sec_setup):
    """NFR 4.1: Deduplication engine executes in under 2 seconds across large candidate pools."""
    cat = sec_setup["cat"]
    s1 = sec_setup["s1"]

    # Seed 200 open tickets in database
    tickets_to_seed = []
    for i in range(200):
        tickets_to_seed.append(Ticket(
            ticket_id=f"TKT-BENCH-{i:04d}",
            student_id=s1.id,
            category_id=cat.id,
            location=f"Hostel Block {i % 5}, Floor {i % 4}",
            description=f"Automated benchmark grievance fault report description #{i} with light fixture issues",
            status=TicketStatus.OPEN.value
        ))
    db_session.bulk_save_objects(tickets_to_seed)
    db_session.commit()

    # Time deduplication check
    start_time = time.perf_counter()
    matches = DeduplicationEngine.check_duplicates(
        db=db_session,
        category_id=cat.id,
        location="Hostel Block 1, Floor 2",
        description="Light fixture flickering in hostel block 1 floor 2"
    )
    duration_seconds = time.perf_counter() - start_time

    # NFR 4.1 requirement is < 2.0 seconds; should complete in < 0.25 seconds
    assert duration_seconds < 2.0
    assert len(matches) > 0
    assert matches[0]["similarity_score"] >= 50.0

def test_admin_queue_sorting_performance(client, sec_setup):
    """NFR 4.1: Queue sorting & filtering executes in under 2 seconds."""
    admin_header = sec_setup["admin_header"]

    start_time = time.perf_counter()
    resp = client.get("/api/tickets/admin-queue?sort=oldest_unresolved", headers=admin_header)
    duration_seconds = time.perf_counter() - start_time

    assert resp.status_code == 200
    assert duration_seconds < 2.0
