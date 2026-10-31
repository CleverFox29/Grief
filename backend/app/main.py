"""Campus Grievance Addressal System (CGAS) - Main Application Entrypoint."""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db
from app.models import Category
from app.api import auth_router

# Lifecycle manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure uploads directory exists on startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for CS1207 Object Oriented Programming Lab Project: Campus Grievance Addressal System.",
    lifespan=lifespan
)

# Configure CORS for multi-device web clients (desktop & phone)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for development / campus network
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix=settings.API_PREFIX)

# Mount uploads static directory for photo proof
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/", tags=["Root"])
def read_root():
    """System information and operational status."""
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "docs_url": "/docs"
    }

@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check verifying database connectivity and configuration."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        category_count = db.query(Category).count()
        return {
            "status": "healthy",
            "database": "connected",
            "active_categories": category_count,
            "version": settings.VERSION
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}"
        }
