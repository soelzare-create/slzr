"""Accounting service — the only place ledger entries are created.

Sales and purchasing call these when a document is finalized, rather than
writing to `financial_documents` themselves.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.accounting import FinancialDocument
from app.models.enums import FinancialType
from app.models.party import Party


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


# --- balances & summary (فاز ۵) -------------------------------------------
#
# A party's balance = مجموع دخل (فروش به او) − مجموع خرج (خرید از او).
# Positive  -> the party owes us   (طلب ما از او).
# Negative  -> we owe the party    (بدهی ما به او).


def _income_expense(db: Session, party_id: int | None = None) -> dict[str, float]:
    """Sum income and expense (optionally for a single party)."""
    stmt = select(
        FinancialDocument.type,
        func.coalesce(func.sum(FinancialDocument.amount), 0),
    ).group_by(FinancialDocument.type)
    if party_id is not None:
        stmt = stmt.where(FinancialDocument.party_id == party_id)
    totals = {"income": 0.0, "expense": 0.0}
    for ftype, amount in db.execute(stmt):
        totals[ftype.value] = float(amount)
    return totals


def party_balance(db: Session, party_id: int) -> dict:
    t = _income_expense(db, party_id)
    return {
        "party_id": party_id,
        "income": t["income"],
        "expense": t["expense"],
        "balance": t["income"] - t["expense"],
    }


def all_party_balances(db: Session) -> list[dict]:
    """Net balance for every party that has any financial activity."""
    rows = db.execute(
        select(
            FinancialDocument.party_id,
            FinancialDocument.type,
            func.coalesce(func.sum(FinancialDocument.amount), 0),
        )
        .where(FinancialDocument.party_id.is_not(None))
        .group_by(FinancialDocument.party_id, FinancialDocument.type)
    ).all()

    agg: dict[int, dict[str, float]] = {}
    for party_id, ftype, amount in rows:
        entry = agg.setdefault(party_id, {"income": 0.0, "expense": 0.0})
        entry[ftype.value] = float(amount)

    result = []
    for party_id, t in agg.items():
        party = db.get(Party, party_id)
        result.append(
            {
                "party_id": party_id,
                "party_name": party.name if party else None,
                "income": t["income"],
                "expense": t["expense"],
                "balance": t["income"] - t["expense"],
            }
        )
    # largest absolute balance first — the parties that matter most
    result.sort(key=lambda r: abs(r["balance"]), reverse=True)
    return result


def summary(db: Session) -> dict:
    """Company-wide totals: total income, total expense, net."""
    t = _income_expense(db)
    return {
        "income": t["income"],
        "expense": t["expense"],
        "net": t["income"] - t["expense"],
    }
