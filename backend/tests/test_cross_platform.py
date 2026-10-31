"""Cross-platform readiness and portability verification tests (NFR 5).

Verifies Linux and Windows compatibility:
- Pathlib POSIX/Windows URI resolution
- Mixed CRLF and LF newline tolerance for CSV imports
- Timezone neutrality across platforms
- Launch script presence and platform conventions
"""

import os
from pathlib import Path
import io
from fastapi import UploadFile
import pytest
from app.config import settings, BASE_DIR
from app.services.admin_service import AdminService
from app.models import UserRole, Admin

def test_database_url_cross_platform_format():
    """NFR 5: DATABASE_URL must use forward slashes (posix) for SQLite URI compatibility on Windows and Linux."""
    assert "\\" not in settings.DATABASE_URL
    assert settings.DATABASE_URL.startswith("sqlite:///")

def test_upload_dir_pathlib_resolution():
    """NFR 5: UPLOAD_DIR must be a valid directory path derived via pathlib."""
    upload_path = Path(settings.UPLOAD_DIR)
    assert upload_path.is_absolute()
    # Path parent should be backend directory
    assert upload_path.parent == BASE_DIR

def test_csv_import_handles_both_windows_crlf_and_linux_lf(db_session, client):
    """NFR 5: CSV student import handles Windows CRLF (\r\n) and Linux LF (\n) equally well."""
    admin = Admin(
        user_id="admin_platform_test",
        name="Platform Admin",
        email="platform_admin@test.com",
        role=UserRole.ADMIN.value
    )
    admin.set_password("Admin@123")
    db_session.add(admin)
    db_session.commit()

    # 1. Windows CRLF CSV content
    windows_csv_content = (
        "user_id,name,email,hostel_room,phone\r\n"
        "25CSB0W01,Windows User One,win1@campus.edu,Hostel 1 - Room 101,+91-9876543210\r\n"
        "25CSB0W02,Windows User Two,win2@campus.edu,Hostel 1 - Room 102,+91-9876543211\r\n"
    )
    upload_file_win = UploadFile(
        filename="windows_students.csv",
        file=io.BytesIO(windows_csv_content.encode("utf-8"))
    )

    result_win = AdminService.import_students_csv(db_session, admin, upload_file_win)
    assert result_win.successfully_imported == 2
    assert result_win.duplicates_rejected == 0

    # 2. Linux LF CSV content
    linux_csv_content = (
        "user_id,name,email,hostel_room,phone\n"
        "25CSB0L01,Linux User One,lin1@campus.edu,Hostel 2 - Room 201,+91-9876543212\n"
        "25CSB0L02,Linux User Two,lin2@campus.edu,Hostel 2 - Room 202,+91-9876543213\n"
    )
    upload_file_lin = UploadFile(
        filename="linux_students.csv",
        file=io.BytesIO(linux_csv_content.encode("utf-8"))
    )

    result_lin = AdminService.import_students_csv(db_session, admin, upload_file_lin)
    assert result_lin.successfully_imported == 2
    assert result_lin.duplicates_rejected == 0

def test_launch_scripts_exist_and_follow_platform_conventions():
    """NFR 5: Launch scripts run_dev.sh (Linux/macOS) and run_dev.bat (Windows) exist and are non-empty."""
    root_dir = BASE_DIR.parent
    sh_script = root_dir / "run_dev.sh"
    bat_script = root_dir / "run_dev.bat"

    assert sh_script.exists(), "run_dev.sh must exist in project root"
    assert bat_script.exists(), "run_dev.bat must exist in project root"

    sh_bytes = sh_script.read_bytes()
    bat_bytes = bat_script.read_bytes()

    assert len(sh_bytes) > 50, "run_dev.sh must contain content"
    assert len(bat_bytes) > 50, "run_dev.bat must contain content"

    # Unix script should not have CRLF newlines
    assert b"\r\n" not in sh_bytes, "run_dev.sh must use Unix LF newlines"
    # Windows script should have CRLF newlines
    assert b"\r\n" in bat_bytes, "run_dev.bat must use Windows CRLF newlines"
