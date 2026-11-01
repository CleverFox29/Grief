"""Database initialization and initial dataset seeder for MongoDB."""

import sys
from pathlib import Path

# Add backend directory to path if run standalone
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.database import connect_db
from app.models import (
    Category,
    StaffRecord,
    Student,
    Admin,
    UserRole,
    AuditLog,
    AuditAction
)
from app.core.security import hash_password

DEFAULT_CATEGORIES = [
    {"name": "Plumbing", "description": "Issues related to water supply, leaks, taps, drainage, and washrooms."},
    {"name": "Carpentry", "description": "Repairs for doors, windows, beds, cupboards, desks, and wooden furniture."},
    {"name": "Electrical", "description": "Failures in lights, fans, power sockets, air conditioning, and switchboards."},
    {"name": "Masonry", "description": "Structural repairs, tile replacements, wall plastering, and ceiling seepage."},
    {"name": "Administrative", "description": "Hostel room allotments, ID cards, mess clearance, and official requests."},
    {"name": "Security", "description": "Campus safety concerns, lost/found items, gate passes, and emergency reporting."}
]

DEFAULT_STAFF = [
    {"name": "Rajesh Kumar (Plumbing)", "contact": "+91-9876543201", "category_name": "Plumbing", "notes": "Hostel Block A & B plumber"},
    {"name": "Manoj Sharma (Carpentry)", "contact": "+91-9876543202", "category_name": "Carpentry", "notes": "Main campus carpenter"},
    {"name": "Sunil Verma (Electrical)", "contact": "+91-9876543203", "category_name": "Electrical", "notes": "Night shift & day shift electrician"},
    {"name": "Vikram Singh (Masonry)", "contact": "+91-9876543204", "category_name": "Masonry", "notes": "Civil maintenance worker"},
    {"name": "Anita Desai (Administrative)", "contact": "+91-9876543205", "category_name": "Administrative", "notes": "Student affairs superintendent"},
    {"name": "Devendra Pal (Security)", "contact": "+91-9876543206", "category_name": "Security", "notes": "Chief security warden"}
]

def seed_database():
    """Ensure indexes and seed initial data into MongoDB."""
    print("Connecting to MongoDB and ensuring indexes...")
    connect_db()

    Category.ensure_indexes()
    StaffRecord.ensure_indexes()
    Student.ensure_indexes()
    Admin.ensure_indexes()
    AuditLog.ensure_indexes()
    
    try:
        # 1. Seed Categories
        category_map = {}
        for cat_data in DEFAULT_CATEGORIES:
            existing = Category.objects(name=cat_data["name"]).first()
            if not existing:
                category = Category(name=cat_data["name"], description=cat_data["description"])
                category.save()
                category_map[cat_data["name"]] = category
                print(f"Added Category: {cat_data['name']}")
            else:
                category_map[cat_data["name"]] = existing

        # 2. Seed Staff Records
        for staff in DEFAULT_STAFF:
            existing_staff = StaffRecord.objects(name=staff["name"]).first()
            if not existing_staff:
                cat = category_map.get(staff["category_name"])
                staff_rec = StaffRecord(
                    name=staff["name"],
                    contact=staff["contact"],
                    category_id=cat.id if cat else None,
                    notes=staff["notes"]
                )
                staff_rec.save()
                print(f"Added Staff: {staff['name']}")

        # 3. Seed Default Admin User
        admin_user = Admin.objects(user_id="admin01").first()
        if not admin_user:
            admin_user = Admin(
                user_id="admin01",
                name="Chief Administrator",
                email="admin@campus.edu",
                phone="+91-9999900001",
                password_hash=hash_password("Admin@123"),
                role=UserRole.ADMIN.value,
                department="Campus Facilities & Maintenance",
                admin_level="SUPER_ADMIN"
            )
            admin_user.save()
            print("Added Default Admin: admin01 (password: Admin@123)")

        # 4. Seed Default Student User (Group II-8 authors)
        student_user = Student.objects(user_id="25CSB0A22").first()
        if not student_user:
            student_user = Student(
                user_id="25CSB0A22",
                name="Soham Siddhartha Roy",
                email="soham.roy@campus.edu",
                phone="+91-9999900022",
                password_hash=hash_password("Student@123"),
                role=UserRole.STUDENT.value,
                enrollment_no="25CSB0A22",
                hostel_room="Hostel 3, Room 204"
            )
            student_user.save()
            print("Added Default Student: 25CSB0A22 (password: Student@123)")

        # 5. Log audit initialization
        audit = AuditLog(
            action=AuditAction.CATEGORY_CREATED.value,
            entity_type="SYSTEM",
            details="Database schema initialized with default categories, staff, and initial users."
        )
        audit.save()

        print("MongoDB seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        raise e

if __name__ == "__main__":
    seed_database()
