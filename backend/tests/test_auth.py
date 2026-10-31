"""Integration tests for Phase 2: Authentication, lockout, and OTP workflows."""

import pytest
from app.models import Student, Admin, UserRole
from app.core.security import hash_password

@pytest.fixture
def seeded_users(db_session):
    """Seed test student and admin accounts."""
    student = Student(
        user_id="25CSB0A22",
        name="Soham Siddhartha Roy",
        email="soham.roy@campus.edu",
        role=UserRole.STUDENT.value,
        enrollment_no="25CSB0A22",
        hostel_room="H3-204"
    )
    student.set_password("Student@123")

    admin = Admin(
        user_id="admin01",
        name="Chief Administrator",
        email="admin@campus.edu",
        role=UserRole.ADMIN.value,
        department="Maintenance",
        admin_level="SUPER_ADMIN"
    )
    admin.set_password("Admin@123")

    db_session.add_all([student, admin])
    db_session.commit()
    return student, admin

def test_successful_student_login(client, seeded_users):
    """F1: Successful student login with correct credentials and role."""
    response = client.post("/api/auth/login", json={
        "user_id": "25CSB0A22",
        "password": "Student@123",
        "role": "STUDENT"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in_minutes"] == 15
    assert data["user"]["user_id"] == "25CSB0A22"
    assert data["user"]["role"] == "STUDENT"
    assert data["user"]["enrollment_no"] == "25CSB0A22"

def test_successful_admin_login(client, seeded_users):
    """F1: Successful admin login with correct credentials and role."""
    response = client.post("/api/auth/login", json={
        "user_id": "admin01",
        "password": "Admin@123",
        "role": "ADMIN"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["department"] == "Maintenance"

def test_role_mismatch_rejection(client, seeded_users):
    """F1: Logging in with wrong role selection is rejected."""
    response = client.post("/api/auth/login", json={
        "user_id": "25CSB0A22",
        "password": "Student@123",
        "role": "ADMIN"  # Student trying to log in as ADMIN
    })
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_account_lockout_after_five_failed_attempts(client, seeded_users):
    """F2: Lock account for 15 minutes after 5 failed password attempts."""
    payload = {
        "user_id": "25CSB0A22",
        "password": "WrongPassword!",
        "role": "STUDENT"
    }

    # Attempts 1 to 4 should return 401 with remaining count
    for i in range(1, 5):
        resp = client.post("/api/auth/login", json=payload)
        assert resp.status_code == 401
        assert f"{5 - i} attempt(s) remaining" in resp.json()["detail"]

    # 5th failed attempt should lock account with 423
    resp5 = client.post("/api/auth/login", json=payload)
    assert resp5.status_code == 423
    assert "Account is now locked for 15 minutes" in resp5.json()["detail"]

    # 6th attempt (even with correct password) should remain locked
    correct_payload = {
        "user_id": "25CSB0A22",
        "password": "Student@123",
        "role": "STUDENT"
    }
    resp6 = client.post("/api/auth/login", json=correct_payload)
    assert resp6.status_code == 423
    assert "Account is locked" in resp6.json()["detail"]

def test_otp_request_and_password_reset(client, seeded_users):
    """F3, U2: Request OTP and reset password successfully."""
    # 1. Request OTP
    otp_resp = client.post("/api/auth/request-otp", json={"user_id": "25CSB0A22"})
    assert otp_resp.status_code == 200
    otp_data = otp_resp.json()
    otp_code = otp_data["otp_preview"]
    assert len(otp_code) == 6
    assert otp_data["expires_in_minutes"] == 5

    # 2. Reset password with invalid OTP code
    bad_reset = client.post("/api/auth/reset-password", json={
        "user_id": "25CSB0A22",
        "otp_code": "000000",
        "new_password": "NewSecretPassword@123"
    })
    assert bad_reset.status_code == 400
    assert "Invalid or expired OTP" in bad_reset.json()["detail"]

    # 3. Reset password with valid OTP code
    good_reset = client.post("/api/auth/reset-password", json={
        "user_id": "25CSB0A22",
        "otp_code": otp_code,
        "new_password": "NewSecretPassword@123"
    })
    assert good_reset.status_code == 200
    assert good_reset.json()["success"] is True

    # 4. Old password should no longer work
    old_login = client.post("/api/auth/login", json={
        "user_id": "25CSB0A22",
        "password": "Student@123",
        "role": "STUDENT"
    })
    assert old_login.status_code == 401

    # 5. New password works
    new_login = client.post("/api/auth/login", json={
        "user_id": "25CSB0A22",
        "password": "NewSecretPassword@123",
        "role": "STUDENT"
    })
    assert new_login.status_code == 200

    # 6. Reusing the same OTP should fail (single-use constraint)
    reuse_reset = client.post("/api/auth/reset-password", json={
        "user_id": "25CSB0A22",
        "otp_code": otp_code,
        "new_password": "AnotherPassword@123"
    })
    assert reuse_reset.status_code == 400

def test_get_current_user_profile(client, seeded_users):
    """NFR 4.2: Protected endpoint requires valid Bearer token."""
    # Without token
    no_auth = client.get("/api/auth/me")
    assert no_auth.status_code == 401

    # Login to obtain token
    login_resp = client.post("/api/auth/login", json={
        "user_id": "admin01",
        "password": "Admin@123",
        "role": "ADMIN"
    })
    token = login_resp.json()["access_token"]

    # With valid token
    auth_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert auth_resp.status_code == 200
    data = auth_resp.json()
    assert data["user_id"] == "admin01"
    assert data["role"] == "ADMIN"
    assert data["department"] == "Maintenance"
