"""Django settings for the DaranX accounting & invoicing system (Phase 1).

Philosophy: «همه چیز سر جای خودش» — modular monolith, one Django project with
apps aligned to the company's departments. UI language is Persian (RTL); code and
comments are English.

Database defaults to SQLite for zero-setup development; point ``DATABASE_URL`` at
PostgreSQL for production (integrity, atomic multi-table transactions,
``select_for_update`` row locking).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present (never committed).
load_dotenv(BASE_DIR / ".env")


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me-in-production")
DEBUG = _env_bool("DEBUG", True)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local apps (department-aligned modular monolith)
    "apps.core",
    "apps.accounts",
    "apps.accounting",
    "apps.procurement",
    "apps.sales",
    "apps.technical",
    "apps.management",
    "apps.warehouse",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "daranx.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "daranx.wsgi.application"


# --- Database ---------------------------------------------------------------
# DATABASE_URL like: postgresql+psycopg://user:pass@host:5432/dbname
def _database_from_url(url: str) -> dict:
    from urllib.parse import urlparse, unquote

    parsed = urlparse(url)
    if parsed.scheme.startswith("sqlite"):
        name = url.split("///", 1)[-1] or str(BASE_DIR / "daranx.db")
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": name}
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (parsed.path or "").lstrip("/"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
    }


_database_url = os.getenv("DATABASE_URL", "")
if _database_url:
    DATABASES = {"default": _database_from_url(_database_url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "daranx.db",
        }
    }


AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 6}},
]

# --- i18n / RTL -------------------------------------------------------------
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF + JWT --------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_MINUTES", "480"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- CORS (React dev server) ------------------------------------------------
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# --- Business rules (Phase 1) ----------------------------------------------
# Section 6: minimum sale margin per line = purchase price × 1.05.
MIN_MARGIN_MULTIPLIER = float(os.getenv("MIN_MARGIN_MULTIPLIER", "1.05"))
# Section 5: soft reservation window for a confirmed proforma.
SOFT_RESERVATION_HOURS = int(os.getenv("SOFT_RESERVATION_HOURS", "48"))

# Initial admin (seed)
FIRST_ADMIN_PHONE = os.getenv("FIRST_ADMIN_PHONE", "09120000000")
FIRST_ADMIN_PASSWORD = os.getenv("FIRST_ADMIN_PASSWORD", "admin1234")
FIRST_ADMIN_NAME = os.getenv("FIRST_ADMIN_NAME", "مدیر سیستم")
