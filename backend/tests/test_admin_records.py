"""Integration tests for Phase 6: Admin Master Data, CSV Import, Auditing, and Reports (F14, F15, U8, U9)."""

import io
from datetime import datetime, timezone
import pytest
from app.models import Admin, Student, Category, StaffRecord, Ticket, TicketStatus, UserRole

@pytest.fixture
def admin_setup(client, db_session):
    """Seed test admin and return auth header."""
    admin = Admin(
        user_id="superadmin",
        name="Super Admin",
        email="superadmin@campus.edu",
        role=UserRole.ADMIN.value,
        department="Central Administration"
    )
    admin.set_password("Admin@123")
    db_session.add(admin)
    db_session.commit()

    login = client.post("/api/auth/login", json={"user_id": "superadmin", "password": "Admin@123", "role": "ADMIN"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_add_student_manually_and_reject_duplicates(client, admin_setup):
    """F14, U8: Add single student and reject duplicate ID."""
    header = admin_setup

    payload = {
        "user_id": "25CSB0A99",
        "name": "Aniket Borkar",
        "email": "aniket.borkar@campus.edu",
        "password": "Password@123",
        "hostel_room": "Hostel 3, Room 101"
    }

    resp = client.post("/api/admin/students", headers=header, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == "25CSB0A99"
    assert data["name"] == "Aniket Borkar"

    # Duplicate ID rejection (U8 Exception)
    dup_resp = client.post("/api/admin/students", headers=header, json=payload)
    assert dup_resp.status_code == 400
    assert "Duplicate student IDs are rejected" in dup_resp.json()["detail"]

def test_import_students_csv_with_duplicate_handling(client, admin_setup):
    """F14, U8: Bulk upload student records via CSV with duplicate rejection."""
    header = admin_setup

    csv_data = (
        "user_id,name,email,hostel_room\n"
        "25CSB0A12,Jibendra Kumar Garai,jibendra@campus.edu,H3-102\n"
        "25CSB0A54,Chaitanya Sathone,chaitanya@campus.edu,H3-103\n"
        "25CSB0A12,Duplicate Jibendra,dup@campus.edu,H3-102\n"  # Duplicate ID in file
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    resp = client.post(
        "/api/admin/students/import-csv",
        headers=header,
        files={"file": ("students.csv", file_bytes, "text/csv")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_processed"] == 3
    assert data["successfully_imported"] == 2
    assert data["duplicates_rejected"] == 1
    assert len(data["errors"]) >= 1

def test_staff_record_management(client, admin_setup, db_session):
    """F14, U8: Add and update maintenance staff records."""
    header = admin_setup

    # Create category first
    cat = Category(name="Masonry Work")
    db_session.add(cat)
    db_session.commit()

    # Create staff
    create_resp = client.post("/api/admin/staff", headers=header, json={
        "name": "Babu Lal",
        "contact": "+91-9876543299",
        "category_id": cat.id,
        "notes": "Experienced mason"
    })
    assert create_resp.status_code == 201
    staff_id = create_resp.json()["id"]

    # Update staff
    update_resp = client.patch(f"/api/admin/staff/{staff_id}", headers=header, json={
        "notes": "Lead civil maintenance mason",
        "is_active": True
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["notes"] == "Lead civil maintenance mason"

def test_category_crud_and_deletion_safeguard(client, admin_setup, db_session):
    """F14, U8: Create category, verify deletion blocked with open tickets, delete when clear."""
    header = admin_setup

    # 1. Create Category
    cat_resp = client.post("/api/admin/categories", headers=header, json={
        "name": "HVAC Cooling",
        "description": "Air conditioning and ventilation"
    })
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    # 2. Add an open ticket in this category
    student = Student(user_id="std_test", name="T Student", email="ts@test.com", role=UserRole.STUDENT.value)
    student.set_password("Pass123")
    db_session.add(student)
    db_session.flush()

    ticket = Ticket(
        ticket_id="TKT-HVAC-01",
        student_id=student.id,
        category_id=cat_id,
        location="Server Room",
        description="AC unit leaking refrigerant",
        status=TicketStatus.OPEN.value
    )
    db_session.add(ticket)
    db_session.commit()

    # 3. Attempting to delete should be blocked (F14 safeguard)
    del_blocked = client.delete(f"/api/admin/categories/{cat_id}", headers=header)
    assert del_blocked.status_code == 400
    assert "active open/in-progress tickets and cannot be deleted" in del_blocked.json()["detail"]

    # 4. Resolve the ticket
    ticket.status = TicketStatus.RESOLVED.value
    db_session.commit()

    # 5. Now deletion succeeds
    del_ok = client.delete(f"/api/admin/categories/{cat_id}", headers=header)
    assert del_ok.status_code == 200
    assert "successfully deleted" in del_ok.json()["message"]

def test_view_immutable_audit_logs(client, admin_setup):
    """F15, NFR 4.2: Retrieve immutable audit logs of ticket and security actions."""
    header = admin_setup

    resp = client.get("/api/admin/audit-logs", headers=header)
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    assert any("CATEGORY" in a or "STUDENT" in a or "LOGIN" in a for a in actions)

def test_summary_reports_and_csv_export(client, admin_setup, db_session):
    """F15, U9: View summary report by category & status and download CSV export."""
    header = admin_setup

    # Query JSON report
    report_resp = client.get("/api/admin/reports", headers=header)
    assert report_resp.status_code == 200
    data = report_resp.json()
    assert "total_tickets" in data
    assert "summary" in data
    assert isinstance(data["summary"], list)

    # Download CSV report
    csv_resp = client.get("/api/admin/reports/export", headers=header)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_text = csv_resp.text
    assert "Campus Grievance Addressal System (CGAS) - Summary Report" in csv_text
    assert "Category,OPEN,IN PROGRESS,RESOLVED,CLOSED,DUPLICATE,Total Tickets" in csv_text
