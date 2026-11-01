"""Vercel Serverless Function entrypoint for CGAS FastAPI backend."""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app.*' imports resolve
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import connect_db
from app.main import app

# Ensure database is connected on cold start
try:
    connect_db()
    if os.getenv("AUTO_SEED", "false").lower() in ("true", "1"):
        from app.models import Category
        from app.seed import seed_database
        if Category.objects.count() == 0:
            seed_database()
except Exception:
    pass
