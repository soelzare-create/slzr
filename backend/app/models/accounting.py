"""Financial document model — bounded context: accounting.

Rule (blueprint): accounting only records financial events. It does not know
where a project stands; it reacts to invoices (income) and purchases (expense).

A document can be attributed to a sales invoice, a purchase, and/or a party
directly — so accounting can compute one net balance per party (what they owe
us for sales, minus what we owe them for purchases).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import FinancialType, PaymentDirection
from app.models.mixins import TimestampMixin


class FinancialDocument(Base, TimestampMixin):
    """اسناد مالی."""

    __tablename__ = "financial_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # فاکتور فروش مرتبط (برای درآمد)
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchases.id"), index=True
    )  # سند خرید مرتبط (برای هزینه)
    party_id: Mapped[int | None] = mapped_column(
        ForeignKey("parties.id"), index=True
    )  # طرف‌حساب (برای محاسبهٔ مانده)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # مبلغ
    type: Mapped[FinancialType] = mapped_column(
        Enum(FinancialType, native_enum=False, length=10), nullable=False
    )  # نوع: دخل/خرج

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FinancialDocument {self.id} {self.type.value} {self.amount}>"


class Payment(Base, TimestampMixin):
    """پرداخت‌ها و دریافت‌ها — تراکنش نقدیِ واقعی (جدا از سند تعهدی فاکتور/خرید).

    یک فاکتور می‌تواند چند دریافت داشته باشد (مثلاً بخشی نقد، مابقی دو هفته بعد)؛
    مبلغ پرداخت‌شدهٔ فاکتور = مجموع دریافت‌های آن.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[PaymentDirection] = mapped_column(
        Enum(PaymentDirection, native_enum=False, length=10), nullable=False
    )  # دریافت یا پرداخت
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # مبلغ
    paid_at: Mapped[date | None] = mapped_column(Date)  # تاریخ تراکنش
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # فاکتور مرتبط (برای دریافت)
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchases.id"), index=True
    )  # سند خرید مرتبط (برای پرداخت)
    party_id: Mapped[int | None] = mapped_column(
        ForeignKey("parties.id"), index=True
    )  # طرف‌حساب
    recorder_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )  # کاربر ثبت‌کننده
    note: Mapped[str | None] = mapped_column(String(500))  # توضیح

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Payment {self.id} {self.direction.value} {self.amount}>"
