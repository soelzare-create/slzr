"""Customer model — bounded context: CRM.

Rule (blueprint): the CRM only holds customer information. It knows nothing
about invoices or inventory.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class Customer(Base, TimestampMixin):
    """مشتری‌ها."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # نام مشتری/سازمان
    phone: Mapped[str | None] = mapped_column(String(30), index=True)  # شماره تماس
    address: Mapped[str | None] = mapped_column(String(500))  # نشانی
    contact_date: Mapped[date | None] = mapped_column(Date)  # تاریخ آشنایی
    referral_source: Mapped[str | None] = mapped_column(String(200))  # مدل آشنایی

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Customer {self.id} {self.name}>"
