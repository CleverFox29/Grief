"""Tests for configuration settings with os.getenv, .env, and default fallback resolution."""

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from app.config import Settings, settings

def test_default_fallbacks():
    """Verify built-in default values exist when not specified."""
    assert settings.VERSION == "1.0.0"
    assert settings.API_PREFIX == "/api"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert settings.MAX_FAILED_LOGIN_ATTEMPTS == 5
    assert settings.ACCOUNT_LOCKOUT_MINUTES == 15
    assert settings.OTP_VALIDITY_MINUTES == 5
    assert settings.REOPEN_WINDOW_DAYS == 7
    assert settings.MAX_UPLOAD_SIZE_BYTES == 5 * 1024 * 1024
    assert settings.MONGODB_DB_NAME == "cgas_db"


def test_os_environ_precedence(monkeypatch):
    """Verify that an operating system environment variable takes precedence over defaults and .env."""
    monkeypatch.setenv("PROJECT_NAME", "Overridden By OS Environment")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    custom_settings = Settings()
    assert custom_settings.PROJECT_NAME == "Overridden By OS Environment"
    assert custom_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 45
    assert custom_settings.get("PROJECT_NAME") == "Overridden By OS Environment"


def test_dotenv_file_loading_and_fallback(tmp_path, monkeypatch):
    """Verify reading values from a .env file when OS env var is not set."""
    test_env = tmp_path / ".env"
    test_env.write_text("PROJECT_NAME=Custom From Dotenv\nREOPEN_WINDOW_DAYS=14\nCUSTOM_VAR=loaded_from_file\n", encoding="utf-8")

    # Clear any potential OS environment overrides for these keys
    monkeypatch.delenv("PROJECT_NAME", raising=False)
    monkeypatch.delenv("REOPEN_WINDOW_DAYS", raising=False)
    monkeypatch.delenv("CUSTOM_VAR", raising=False)

    class CustomTestSettings(Settings):
        model_config = Settings.model_config.copy()
        model_config["env_file"] = (test_env,)

    # Load into os.environ with override=False
    load_dotenv(dotenv_path=test_env, override=False)

    custom_s = CustomTestSettings()
    assert custom_s.PROJECT_NAME == "Custom From Dotenv"
    assert custom_s.REOPEN_WINDOW_DAYS == 14
    # Default fallback remains untouched
    assert custom_s.VERSION == "1.0.0"
    # settings.get resolves the custom variable
    assert custom_s.get("CUSTOM_VAR") == "loaded_from_file"


def test_settings_get_fallback():
    """Verify settings.get returns custom default when key is neither in os.environ nor .env."""
    assert settings.get("NON_EXISTENT_KEY", "fallback_value") == "fallback_value"
    assert settings.get("PROJECT_NAME") == settings.PROJECT_NAME


def test_settings_dictionary_style_access():
    """Verify dictionary-style indexing settings['KEY']."""
    assert settings["PROJECT_NAME"] == settings.PROJECT_NAME
    assert settings["VERSION"] == "1.0.0"


def test_database_url_and_mongodb_url_sync(monkeypatch):
    """Verify DATABASE_URL syncs with MONGODB_URL."""
    custom_db = "mongodb://custom-host:27017/custom_db"
    monkeypatch.setenv("DATABASE_URL", custom_db)
    monkeypatch.delenv("MONGODB_URL", raising=False)

    custom_s = Settings(_env_file=())
    assert custom_s.MONGODB_URL == custom_db
