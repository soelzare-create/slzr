"""Accounting schemas — the ledger, per-party balances, and the summary (فاز ۵)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FinancialType, PaymentDirection


class FinancialDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: FinancialType
    amount: float
    party_id: int | None
    invoice_id: int | None
    purchase_id: int | None
    created_at: datetime


class PartyBalanceOut(BaseModel):
    party_id: int
    party_name: str | None = None
    income: float  # فروش به او
    expense: float  # خرید از او
    balance: float  # مانده (مثبت: طلب ما، منفی: بدهی ما)


class AccountingSummaryOut(BaseModel):
    income: float          # مجموع فروش (تعهدی)
    expense: float         # مجموع خرید (تعهدی)
    net: float             # مانده تعهدی
    received: float = 0     # مجموع دریافت‌های نقدی
    paid_out: float = 0     # مجموع پرداخت‌های نقدی
    receivable: float = 0   # طلبِ وصول‌نشده (فروش منهای دریافت)
    payable: float = 0      # بدهیِ پرداخت‌نشده (خرید منهای پرداخت)


class PaymentCreate(BaseModel):
    direction: PaymentDirection
    amount: float = Field(gt=0)
    paid_at: date | None = None
    invoice_id: int | None = None   # برای دریافت بابت فاکتور
    purchase_id: int | None = None  # برای پرداخت بابت خرید
    party_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direction: PaymentDirection
    amount: float
    paid_at: date | None
    invoice_id: int | None
    purchase_id: int | None
    party_id: int | None
    recorder_id: int | None
    note: str | None
    created_at: datetime
