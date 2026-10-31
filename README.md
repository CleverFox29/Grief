# Campus Grievance Addressal System (CGAS)

> CS1207 Object Oriented Programming Lab Project &bull; Version 1.0  
> Group II-8: Soham Siddhartha Roy, Jibendra Kumar Garai, Chaitanya Sathone, Aniket Rajesh Borkar

A web-based portal engineered to replace scattered grievance channels with a unified ticket queue, intelligent duplicate detection, transparent timeline tracking, and measurable grievance resolution across campus facilities.

---

## Architecture & Technology Stack

- **Backend**: Python 3 (FastAPI + SQLAlchemy ORM)
- **Frontend**: React + Vite + Tailwind CSS (Mobile & Desktop Responsive)
- **Database**: SQLite (local development & lab grading) / MySQL ready
- **Duplicate Detection**: RapidFuzz / TF-IDF text similarity engine
- **Testing**: PyTest with in-memory database test fixtures

---

## Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── config.py              # Application settings & security policies
│   │   ├── database.py            # SQLite engine, sessionmaker & pragma config
│   │   ├── main.py                # FastAPI app entrypoint, CORS, static uploads
│   │   ├── seed.py                # Database schema builder & default data seeder
│   │   ├── core/
│   │   │   └── security.py        # Salted bcrypt hashing, JWT tokens, OTPs
│   │   └── models/                # Modular OOP Domain Models (one per entity)
│   │       ├── enums.py           # UserRole, TicketStatus, AuditAction
│   │       ├── base.py            # TimestampMixin and UTC helpers
│   │       ├── user.py            # User (base class), Student, Admin
│   │       ├── staff.py           # StaffRecord (maintenance/admin personnel)
│   │       ├── category.py        # Category (deletion safety guards)
│   │       ├── ticket.py          # Ticket (status lifecycle, duplicate linking)
│   │       ├── ticket_log.py      # TicketLog (immutable audit history)
│   │       ├── feedback.py        # Feedback (1-5 rating & comment)
│   │       ├── notification.py    # Notification (status alert dispatch)
│   │       ├── audit_log.py       # AuditLog (immutable system log)
│   │       └── otp.py             # PasswordResetOTP (5-min single use OTP)
│   ├── tests/
│   │   ├── conftest.py            # Test isolation fixtures
│   │   ├── test_domain_models.py  # 7 unit test suites verifying OOP rules
│   │   └── test_api_health.py     # API root and health check integration tests
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Root responsive layout
│   │   ├── main.jsx
│   │   └── index.css              # Tailwind CSS directives
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── SRS_Campus_Grievance_Addressal_System_Updated (1).pdf
└── README.md
```

---

## Quickstart Guide

### 1. Backend Setup & Tests

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run database migration & initial seed
python app/seed.py

# Run test suite
pytest -v

# Run backend development server
uvicorn app.main:app --reload --port 8000
```

Default seeded credentials:
- **Admin**: ID `admin01` / Password `Admin@123`
- **Student**: ID `25CSB0A22` / Password `Student@123`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser (or on a mobile device on the same local network).
