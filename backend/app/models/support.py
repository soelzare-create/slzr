"""Task model — bounded context: internal task referrals (ارجاعات).

Replaces the old customer ticketing. A task is a piece of work referred from one
employee to another (e.g. sales → technical for installation, or the system →
warehouse to deliver sold goods). The creator can follow its stage; the assignee
drives it to done. Optionally linked to the invoice that spawned it.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import TaskStatus
from app.models.mixins import TimestampMixin


class Task(Base, TimestampMixin):
    """کارهای ارجاع‌شده به کارمندان."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)  # عنوان کار
    description: Mapped[str | None] = mapped_column(String(4000))  # شرح
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # ارجاع‌دهنده
    assigned_to_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # ارجاع‌شونده (مسئول انجام)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=20),
        default=TaskStatus.assigned,
        nullable=False,
    )  # وضعیت
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )  # زمان انجام (مثلاً زمان نصب)
    done_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )  # زمان واقعی انجام‌شدن
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # فاکتور مرتبط (اگر از روی فروش ساخته شده)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task {self.id} {self.title} {self.status.value}>"
