"""Integration tests for Phase 3: Ticket Creation and Deduplication Engine (F4-F7)."""

import io
import pytest
from app.models import Category, Student, Admin, Ticket, TicketStatus, UserRole

@pytest.fixture
def student_auth_header(client, db_session):
    """Seed student and return bearer authorization header."""
    student = Student(
        user_id="25CSB0A22",
        name="Soham Siddhartha Roy",
        email="soham.roy@campus.edu",
        role=UserRole.STUDENT.value,
        enrollment_no="25CSB0A22",
        hostel_room="H3-204"
    )
    student.set_password("Student@123")
    db_session.add(student)
    db_session.commit()

    login_resp = client.post("/api/auth/login", json={
        "user_id": "25CSB0A22",
        "password": "Student@123",
        "role": "STUDENT"
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def seeded_categories(db_session):
    """Seed default categories."""
    cats = [
        Category(name="Plumbing", description="Plumbing issues"),
        Category(name="Electrical", description="Electrical faults"),
        Category(name="Carpentry", description="Carpentry and furniture")
    ]
    db_session.add_all(cats)
    db_session.commit()
    return {c.name: c.id for c in cats}

def test_get_active_categories(client, seeded_categories):
    """Test retrieving active grievance categories."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    names = [c["name"] for c in data]
    assert "Plumbing" in names
    assert "Electrical" in names

def test_deduplication_engine_detects_match(client, db_session, student_auth_header, seeded_categories):
    """F6: Deduplication check warns student of possible duplicate open ticket."""
    cat_id = seeded_categories["Plumbing"]
    student = db_session.query(Student).filter_by(user_id="25CSB0A22").first()

    # Pre-existing open ticket
    existing_ticket = Ticket(
        ticket_id="TKT-2026-0001",
        student_id=student.id,
        category_id=cat_id,
        location="Hostel 3, 2nd Floor Washroom",
        description="Water tap is leaking continuously and overflowing the sink",
        status=TicketStatus.OPEN.value
    )
    db_session.add(existing_ticket)
    db_session.commit()

    # Query duplicate check with similar issue at same location
    check_resp = client.post("/api/tickets/check-duplicates", headers=student_auth_header, json={
        "category_id": cat_id,
        "location": "Hostel 3 2nd floor washroom",
        "description": "Tap leaking water and causing overflow"
    })

    assert check_resp.status_code == 200
    data = check_resp.json()
    assert data["has_duplicates"] is True
    assert data["count"] >= 1
    match = data["matches"][0]
    assert match["ticket_id"] == "TKT-2026-0001"
    assert match["similarity_score"] >= 60.0

    # Query in a different category (Electrical) should yield 0 matches
    elec_check = client.post("/api/tickets/check-duplicates", headers=student_auth_header, json={
        "category_id": seeded_categories["Electrical"],
        "location": "Hostel 3 2nd floor washroom",
        "description": "Tap leaking water"
    })
    assert elec_check.status_code == 200
    assert elec_check.json()["has_duplicates"] is False

def test_create_standard_ticket_with_valid_photo(client, student_auth_header, seeded_categories):
    """F4, F5: Raise a standard grievance with a valid PNG photo."""
    cat_id = seeded_categories["Electrical"]

    # Valid PNG header magic bytes
    valid_png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    fake_file = io.BytesIO(valid_png_content)

    response = client.post(
        "/api/tickets",
        headers=student_auth_header,
        data={
            "category_id": cat_id,
            "location": "Hostel 3, Room 204",
            "description": "Ceiling light tube is flickering constantly",
            "is_confidential": False,
            "action": "CREATE"
        },
        files={"photo": ("light.png", fake_file, "image/png")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ticket_id"].startswith("TKT-")
    assert data["status"] == "OPEN"
    assert data["location"] == "Hostel 3, Room 204"
    assert data["photo_url"] is not None
    assert data["photo_url"].endswith(".png")
    assert data["is_flagged_duplicate"] is False

def test_reject_photo_with_fake_extension(client, student_auth_header, seeded_categories):
    """NFR 4.2: Reject uploaded photo that has wrong binary magic bytes (e.g. text file named .png)."""
    cat_id = seeded_categories["Plumbing"]
    fake_text_content = b"This is plain text pretending to be a photo."
    fake_file = io.BytesIO(fake_text_content)

    response = client.post(
        "/api/tickets",
        headers=student_auth_header,
        data={
            "category_id": cat_id,
            "location": "Room 101",
            "description": "Pipe leaking",
            "action": "CREATE"
        },
        files={"photo": ("fake.png", fake_file, "image/png")}
    )

    assert response.status_code == 400
    assert "Invalid image file type" in response.json()["detail"]

def test_reject_photo_exceeding_5mb(client, student_auth_header, seeded_categories):
    """NFR 4.2: Reject uploaded photo exceeding 5 MB limit."""
    cat_id = seeded_categories["Plumbing"]
    # 5.5 MB file with valid PNG header
    oversized_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * (5500 * 1024)
    fake_file = io.BytesIO(oversized_content)

    response = client.post(
        "/api/tickets",
        headers=student_auth_header,
        data={
            "category_id": cat_id,
            "location": "Room 101",
            "description": "Pipe leaking",
            "action": "CREATE"
        },
        files={"photo": ("huge.png", fake_file, "image/png")}
    )

    assert response.status_code == 400
    assert "exceeds maximum allowed limit of 5 MB" in response.json()["detail"]

def test_support_duplicate_ticket_workflow(client, db_session, student_auth_header, seeded_categories):
    """F7: Student selects 'Support' -> new ticket marked DUPLICATE and linked to parent."""
    cat_id = seeded_categories["Carpentry"]
    student = db_session.query(Student).filter_by(user_id="25CSB0A22").first()

    parent = Ticket(
        ticket_id="TKT-PARENT-100",
        student_id=student.id,
        category_id=cat_id,
        location="Library Study Room 2",
        description="Study table leg broken",
        status=TicketStatus.OPEN.value
    )
    db_session.add(parent)
    db_session.commit()

    # Student chooses to SUPPORT parent
    response = client.post(
        "/api/tickets",
        headers=student_auth_header,
        data={
            "category_id": cat_id,
            "location": "Library Study Room 2",
            "description": "Table leg is wobbling and broken",
            "action": "SUPPORT",
            "parent_ticket_id": parent.id
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "DUPLICATE"
    assert data["parent_ticket_id"] == parent.id

def test_submit_anyway_duplicate_ticket_workflow(client, student_auth_header, seeded_categories):
    """F7: Student selects 'Submit Anyway' -> ticket created OPEN and is_flagged_duplicate=True."""
    cat_id = seeded_categories["Carpentry"]

    response = client.post(
        "/api/tickets",
        headers=student_auth_header,
        data={
            "category_id": cat_id,
            "location": "Library Study Room 2",
            "description": "Chair armrest is cracked",
            "action": "SUBMIT_ANYWAY"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "OPEN"
    assert data["is_flagged_duplicate"] is True
