"""Financial document model — bounded context: accounting.

Rule (blueprint): accounting only records financial events. It does not know
where a project stands; it reacts to invoices (income) and purchases (expense).

A document can be attributed to a sales invoice, a purchase, and/or a party
directly — so accounting can compute one net balance per party (what they owe
us for sales, minus what we owe them for purchases).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import (
    CashAccountType,
    ChequeDirection,
    ChequeStatus,
    FinancialType,
    PaymentDirection,
    PaymentMethod,
)
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


class CashAccount(Base, TimestampMixin):
    """صندوق‌ها و حساب‌های بانکی — جایی که پول نگهداری می‌شود.

    مانده = مانده‌ی اولیه + مجموع دریافت‌ها − مجموع پرداخت‌ها (محاسبه‌شونده).
    """

    __tablename__ = "cash_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # نام حساب
    type: Mapped[CashAccountType] = mapped_column(
        Enum(CashAccountType, native_enum=False, length=10),
        default=CashAccountType.cash,
        nullable=False,
    )  # صندوق یا بانک
    opening_balance: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # مانده‌ی اولیه
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CashAccount {self.id} {self.name}>"


class Payment(Base, TimestampMixin):
    """اسناد دریافت و پرداخت — تراکنش نقدیِ واقعی (جدا از سند تعهدی فاکتور/خرید).

    یک سند می‌تواند به فاکتور/خرید وصل باشد (تسویه‌ی آن)، یا مستقل باشد
    (دریافت متفرقه، یا هزینه‌ی عملیاتی مثل اجاره/حقوق/قبوض). هر سند روی مانده‌ی
    یک حساب مالی (صندوق/بانک) اثر می‌گذارد.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[PaymentDirection] = mapped_column(
        Enum(PaymentDirection, native_enum=False, length=10), nullable=False
    )  # دریافت یا پرداخت
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # مبلغ
    paid_at: Mapped[date | None] = mapped_column(Date)  # تاریخ تراکنش
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=10),
        default=PaymentMethod.cash,
        nullable=False,
    )  # روش
    category: Mapped[str | None] = mapped_column(
        String(120), index=True
    )  # دستهٔ هزینه/درآمد (مثلاً اجاره، حقوق، فروش)
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("cash_accounts.id"), index=True
    )  # حساب مالیِ اثرپذیر
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # فاکتور مرتبط (برای دریافت بابت فروش)
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchases.id"), index=True
    )  # سند خرید مرتبط (برای پرداخت بابت خرید)
    party_id: Mapped[int | None] = mapped_column(
        ForeignKey("parties.id"), index=True
    )  # طرف‌حساب
    recorder_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )  # کاربر ثبت‌کننده
    note: Mapped[str | None] = mapped_column(String(500))  # توضیح

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Payment {self.id} {self.direction.value} {self.amount}>"


class Cheque(Base, TimestampMixin):
    """چک‌های دریافتی و پرداختی — تعهد پرداخت با سررسید (پایهٔ اقساط).

    چند چک با سررسیدهای مختلف روی یک فاکتور/خرید = پرداخت اقساطی. چک تا زمان
    «وصول/پاس‌شدن» اثری روی نقدینگی ندارد؛ هنگام وصول، یک سند دریافت/پرداخت واقعی
    ساخته می‌شود و فاکتور/خرید مرتبط تسویه می‌گردد.
    """

    __tablename__ = "cheques"

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[ChequeDirection] = mapped_column(
        Enum(ChequeDirection, native_enum=False, length=10), nullable=False
    )  # دریافتی یا پرداختی
    number: Mapped[str] = mapped_column(String(60), nullable=False)  # شماره چک
    bank_name: Mapped[str | None] = mapped_column(String(120))  # بانک
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # مبلغ
    due_date: Mapped[date] = mapped_column(Date, nullable=False)  # سررسید
    status: Mapped[ChequeStatus] = mapped_column(
        Enum(ChequeStatus, native_enum=False, length=12),
        default=ChequeStatus.registered,
        nullable=False,
    )  # وضعیت
    party_id: Mapped[int | None] = mapped_column(
        ForeignKey("parties.id"), index=True
    )  # طرف‌حساب (صادرکنندهٔ چک دریافتی / گیرندهٔ چک پرداختی)
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # فاکتور مرتبط (چک دریافتی)
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchases.id"), index=True
    )  # سند خرید مرتبط (چک پرداختی)
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("cash_accounts.id"), index=True
    )  # حسابی که چک هنگام وصول به آن می‌نشیند / از آن پرداخت می‌شود
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id"), index=True
    )  # سند نقدیِ ساخته‌شده هنگام وصول
    recorder_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    note: Mapped[str | None] = mapped_column(String(500))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Cheque {self.id} {self.direction.value} {self.amount} {self.status.value}>"
