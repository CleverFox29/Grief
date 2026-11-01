"""Configuration settings for Campus Grievance Addressal System (CGAS)."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Campus Grievance Addressal System (CGAS)"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database (MongoDB)
    MONGODB_URL: str = "mongodb://localhost:27017/cgas_db"
    MONGODB_DB_NAME: str = "cgas_db"
    DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "cgas-development-secret-key-change-in-production-cs1207"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes session timeout as per NFR 4.2
    
    # Grievance & Account Policies
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5     # Account locks after 5 failed attempts (F2)
    ACCOUNT_LOCKOUT_MINUTES: int = 15      # Locked for 15 minutes (F2)
    OTP_VALIDITY_MINUTES: int = 5          # OTP valid for 5 minutes (NFR 4.2, F3)
    REOPEN_WINDOW_DAYS: int = 7            # Student can reopen within 7 days (F13)
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB max photo upload (F4, NFR 4.2)
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/uploads" if os.getenv("VERCEL") == "1" else str(BASE_DIR / "uploads"))

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR.parent / ".env", BASE_DIR / ".env", ".env"),
        extra="ignore"
    )

    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            self.DATABASE_URL = self.MONGODB_URL
        elif self.DATABASE_URL and self.MONGODB_URL == "mongodb://localhost:27017/cgas_db" and self.DATABASE_URL != self.MONGODB_URL:
            self.MONGODB_URL = self.DATABASE_URL

settings = Settings()
