"""User (team member) model — bounded context: access & security."""
from __future__ import annotations

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    """کاربران (تیم شرکت)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # نام
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), nullable=False
    )  # نقش
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # رمز ورود
    phone: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )  # شماره تماس (used as the login identifier)
    address: Mapped[str | None] = mapped_column(String(500))  # آدرس
    emergency_contact: Mapped[str | None] = mapped_column(String(30))  # تماس اضطراری
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.id} {self.name} ({self.role.value})>"
