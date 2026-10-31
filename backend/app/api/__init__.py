"""API routers for CGAS."""

from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.api.admin import router as admin_router

__all__ = ["auth_router", "tickets_router", "admin_router"]
