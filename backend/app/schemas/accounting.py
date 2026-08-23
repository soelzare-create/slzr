"""Accounting schemas — the ledger, per-party balances, and the summary (فاز ۵)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    CashAccountType,
    ChequeDirection,
    ChequeStatus,
    FinancialType,
    PaymentDirection,
    PaymentMethod,
)


class FinancialDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: FinancialType
    amount: float
    party_id: int | None
    invoice_id: int | None
    purchase_id: int | None
    created_at: datetime


class FinancialDocumentUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    type: FinancialType | None = None
    party_id: int | None = None


class PartyBalanceOut(BaseModel):
    party_id: int
    party_name: str | None = None
    income: float  # فروش به او
    expense: float  # خرید از او
    balance: float  # مانده (مثبت: طلب ما، منفی: بدهی ما)


class AccountingSummaryOut(BaseModel):
    income: float           # مجموع فروش (تعهدی)
    expense: float          # مجموع خرید (تعهدی)
    net: float              # مانده تعهدی
    received: float = 0      # مجموع دریافت‌های نقدی
    paid_out: float = 0      # مجموع پرداخت‌های نقدی
    receivable: float = 0    # طلبِ وصول‌نشده (فروش منهای دریافت)
    payable: float = 0       # بدهیِ پرداخت‌نشده (خرید منهای پرداخت)
    cash_on_hand: float = 0  # موجودی صندوق‌ها و بانک‌ها


# --- cash & bank accounts --------------------------------------------------

class CashAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: CashAccountType = CashAccountType.cash
    opening_balance: float = Field(default=0, ge=0)


class CashAccountOut(BaseModel):
    id: int
    name: str
    type: CashAccountType
    opening_balance: float
    balance: float
    is_active: bool


# --- payment / receipt vouchers -------------------------------------------

class PaymentCreate(BaseModel):
    direction: PaymentDirection
    amount: float = Field(gt=0)
    paid_at: date | None = None
    method: PaymentMethod = PaymentMethod.cash
    category: str | None = Field(default=None, max_length=120)
    account_id: int | None = None
    invoice_id: int | None = None   # دریافت بابت فاکتور
    purchase_id: int | None = None  # پرداخت بابت خرید
    party_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class PaymentUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    paid_at: date | None = None
    method: PaymentMethod | None = None
    category: str | None = Field(default=None, max_length=120)
    account_id: int | None = None
    party_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direction: PaymentDirection
    amount: float
    paid_at: date | None
    method: PaymentMethod
    category: str | None
    account_id: int | None
    invoice_id: int | None
    purchase_id: int | None
    party_id: int | None
    recorder_id: int | None
    note: str | None
    created_at: datetime


class ExpenseCategoryOut(BaseModel):
    category: str
    amount: float


# --- cheques (چک — دریافتی/پرداختی با سررسید، پایهٔ اقساط) -----------------

class ChequeCreate(BaseModel):
    direction: ChequeDirection
    number: str = Field(min_length=1, max_length=60)
    bank_name: str | None = Field(default=None, max_length=120)
    amount: float = Field(gt=0)
    due_date: date
    party_id: int | None = None
    invoice_id: int | None = None   # چک دریافتی بابت فاکتور (قسط)
    purchase_id: int | None = None  # چک پرداختی بابت خرید (قسط)
    account_id: int | None = None
    note: str | None = Field(default=None, max_length=500)


class ChequeClear(BaseModel):
    account_id: int | None = None   # حسابی که چک به آن می‌نشیند/از آن پرداخت می‌شود
    cleared_at: date | None = None  # تاریخ وصول


class ChequeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direction: ChequeDirection
    number: str
    bank_name: str | None
    amount: float
    due_date: date
    status: ChequeStatus
    party_id: int | None
    invoice_id: int | None
    purchase_id: int | None
    account_id: int | None
    payment_id: int | None
    note: str | None
    created_at: datetime
