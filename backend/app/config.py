"""Application configuration, loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "DaranX"
    debug: bool = True

    # Database — SQLite by default so the backend runs with zero setup.
    # Point DATABASE_URL at PostgreSQL for production (see .env.example).
    database_url: str = "sqlite:///./daranx.db"

    # Security
    secret_key: str = "change-me-in-production-please"
    access_token_expire_minutes: int = 480
    algorithm: str = "HS256"

    # Initial admin (seed)
    first_admin_name: str = "مدیر سیستم"
    first_admin_phone: str = "09120000000"
    first_admin_password: str = "admin1234"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
