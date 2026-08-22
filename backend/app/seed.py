"""Seed the database with the first manager account.

Run once after setup:

    python -m app.seed
"""
from __future__ import annotations

from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.enums import UserRole
from app.models.user import User

# Ensure tables exist even if the app hasn't been started yet.
import app.models  # noqa: F401


def seed() -> None:
    from app.db_migrate import auto_add_missing_columns

    Base.metadata.create_all(bind=engine)
    auto_add_missing_columns(engine, Base)
    db = SessionLocal()
    try:
        existing = db.scalar(
            select(User).where(User.phone == settings.first_admin_phone)
        )
        if existing:
            print(f"[seed] admin already exists (phone={existing.phone}); skipping.")
            return

        admin = User(
            name=settings.first_admin_name,
            role=UserRole.manager,
            phone=settings.first_admin_phone,
            password_hash=hash_password(settings.first_admin_password),
        )
        db.add(admin)
        db.commit()
        print(
            "[seed] created manager account:\n"
            f"        phone   : {settings.first_admin_phone}\n"
            f"        password: {settings.first_admin_password}\n"
            "        -> change this password after first login."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
