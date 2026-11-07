"""Configuration settings for Campus Grievance Addressal System (CGAS).

Resolves configuration with priority:
1. Operating system environment (os.environ / os.getenv)
2. .env files (project root, backend directory, or current directory)
3. Default fallbacks defined on settings fields
"""

import os
from pathlib import Path
from typing import Optional, Any
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Candidate .env locations in order of priority:
# 1. Project root directory (.env)
# 2. Backend directory (backend/.env)
# 3. Current working directory (.env)
ENV_CANDIDATE_PATHS = [
    BASE_DIR.parent / ".env",
    BASE_DIR / ".env",
    Path(".env"),
    Path.cwd() / ".env"
]

# Deduplicate paths while preserving order
_UNIQUE_ENV_PATHS = []
for _p in ENV_CANDIDATE_PATHS:
    if _p not in _UNIQUE_ENV_PATHS:
        _UNIQUE_ENV_PATHS.append(_p)

# Ensure environment variables from .env files are also loaded into os.environ
# with override=False so that any pre-existing OS / system environment variables take precedence.
for _env_file in _UNIQUE_ENV_PATHS:
    if _env_file.is_file():
        load_dotenv(dotenv_path=_env_file, override=False)


def get_default_upload_dir() -> str:
    """Determine upload directory fallback with Vercel and local detection."""
    env_upload = os.getenv("UPLOAD_DIR")
    if env_upload:
        return env_upload
    if os.getenv("VERCEL") == "1":
        return "/tmp/uploads"
    return str(BASE_DIR / "uploads")


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
    UPLOAD_DIR: str = Field(default_factory=get_default_upload_dir)
    AUTO_SEED: bool = False

    model_config = SettingsConfigDict(
        env_file=tuple(_UNIQUE_ENV_PATHS),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            self.DATABASE_URL = self.MONGODB_URL
        elif self.DATABASE_URL and self.MONGODB_URL == "mongodb://localhost:27017/cgas_db" and self.DATABASE_URL != self.MONGODB_URL:
            self.MONGODB_URL = self.DATABASE_URL

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve configuration value with priority resolution:
        1. os.environ / os.getenv (OS environment)
        2. Settings property (from .env or model default)
        3. Provided default fallback
        """
        # 1. Check OS environment directly
        for candidate_key in (key, key.upper(), key.lower()):
            if candidate_key in os.environ:
                return os.environ[candidate_key]

        # 2. Check Settings attributes
        for candidate_key in (key, key.upper(), key.lower()):
            if hasattr(self, candidate_key):
                val = getattr(self, candidate_key)
                if val is not None:
                    return val

        # 3. Fallback
        return default

    def __getitem__(self, item: str) -> Any:
        val = self.get(item)
        if val is None:
            raise KeyError(item)
        return val


settings = Settings()
