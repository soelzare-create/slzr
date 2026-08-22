"""Reporting schemas — the management overview (فاز ۷)."""
from __future__ import annotations

from pydantic import BaseModel


class Counts(BaseModel):
    customers: int
    suppliers: int
    activities: int
    products: int
    open_tasks: int


class Finance(BaseModel):
    income: float
    expense: float
    net: float


class StatusBreakdown(BaseModel):
    unpaid: int = 0
    partial: int = 0
    paid: int = 0
    overdue: int = 0
    total: int = 0


class PartyBalanceMini(BaseModel):
    party_id: int
    party_name: str | None = None
    balance: float


class ReportsOverview(BaseModel):
    counts: Counts
    finance: Finance
    invoices: StatusBreakdown
    purchases: StatusBreakdown
    top_debtors: list[PartyBalanceMini]  # بیشترین طلب ما از دیگران
    top_creditors: list[PartyBalanceMini]  # بیشترین بدهی ما به دیگران
