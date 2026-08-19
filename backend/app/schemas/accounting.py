"""Accounting schemas — the ledger, per-party balances, and the summary (فاز ۵)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import FinancialType


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
    income: float
    expense: float
    net: float
