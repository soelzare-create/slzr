"""Financial document model — bounded context: accounting.

Rule (blueprint): accounting only records financial events. It does not know
where a project stands; it reacts to invoices.
"""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import FinancialType
from app.models.mixins import TimestampMixin


class FinancialDocument(Base, TimestampMixin):
    """اسناد مالی."""

    __tablename__ = "financial_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # فاکتور مرتبط
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # مبلغ
    type: Mapped[FinancialType] = mapped_column(
        Enum(FinancialType, native_enum=False, length=10), nullable=False
    )  # نوع: دخل/خرج

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FinancialDocument {self.id} {self.type.value} {self.amount}>"
