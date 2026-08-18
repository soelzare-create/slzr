"""Accounting service — the only place ledger entries are created.

Sales and purchasing call these when a document is finalized, rather than
writing to `financial_documents` themselves.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.accounting import FinancialDocument
from app.models.enums import FinancialType


def record_income(
    db: Session, *, amount: float, party_id: int | None, invoice_id: int | None
) -> FinancialDocument:
    """Record money coming in from a finalized sales invoice (دخل)."""
    doc = FinancialDocument(
        amount=amount,
        type=FinancialType.income,
        party_id=party_id,
        invoice_id=invoice_id,
    )
    db.add(doc)
    db.flush()
    return doc


def record_expense(
    db: Session, *, amount: float, party_id: int | None, purchase_id: int | None
) -> FinancialDocument:
    """Record money going out for a received purchase (خرج)."""
    doc = FinancialDocument(
        amount=amount,
        type=FinancialType.expense,
        party_id=party_id,
        purchase_id=purchase_id,
    )
    db.add(doc)
    db.flush()
    return doc
