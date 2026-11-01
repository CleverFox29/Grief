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
from app.main import app as fastapi_app

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

class VercelPathMiddleware:
    """ASGI middleware to ensure request paths match FastAPI routes on Vercel."""
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            
            # If Vercel rewrote the path to /api/index.py, restore original matched path if available
            if path in ("/api/index.py", "/api/index.py/"):
                if matched_path and matched_path not in ("/api/index.py", "/api/index.py/"):
                    scope["path"] = matched_path
                else:
                    scope["path"] = "/api"
            elif path.startswith("/api/index.py/"):
                scope["path"] = path[len("/api/index.py"):]
        await self.inner_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
