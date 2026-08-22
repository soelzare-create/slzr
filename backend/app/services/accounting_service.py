"""Accounting service — the only place ledger entries are created.

Sales and purchasing call these when a document is finalized, rather than
writing to `financial_documents` themselves.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.accounting import CashAccount, FinancialDocument, Payment
from app.models.enums import (
    FinancialType,
    InvoiceStatus,
    PaymentDirection,
    PaymentMethod,
    PurchaseStatus,
)
from app.models.invoice import Invoice
from app.models.party import Party
from app.models.purchase import Purchase


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
    """Company-wide totals: accrued income/expense, and cash received/paid."""
    t = _income_expense(db)
    received = float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.direction == PaymentDirection.receipt
            )
        )
        or 0
    )
    paid_out = float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.direction == PaymentDirection.payment
            )
        )
        or 0
    )
    return {
        "income": t["income"],
        "expense": t["expense"],
        "net": t["income"] - t["expense"],
        "received": received,
        "paid_out": paid_out,
        "receivable": t["income"] - received,  # طلبِ وصول‌نشدهٔ ما
        "payable": t["expense"] - paid_out,     # بدهیِ پرداخت‌نشدهٔ ما
        "cash_on_hand": cash_on_hand(db),       # مجموع موجودی صندوق‌ها و بانک‌ها
    }


# --- cash & bank accounts (صندوق / بانک) ----------------------------------

def account_balance(db: Session, account: CashAccount) -> float:
    got = float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.direction == PaymentDirection.receipt,
                Payment.account_id == account.id,
            )
        )
        or 0
    )
    out = float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.direction == PaymentDirection.payment,
                Payment.account_id == account.id,
            )
        )
        or 0
    )
    return float(account.opening_balance) + got - out


def accounts_overview(db: Session) -> list[dict]:
    rows = db.scalars(select(CashAccount).order_by(CashAccount.id)).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "type": a.type.value,
            "opening_balance": float(a.opening_balance),
            "balance": account_balance(db, a),
            "is_active": a.is_active,
        }
        for a in rows
    ]


def cash_on_hand(db: Session) -> float:
    return sum(a["balance"] for a in accounts_overview(db))


def expense_by_category(db: Session) -> list[dict]:
    """Group outgoing payments by category — the operating-expense report."""
    rows = db.execute(
        select(
            Payment.category,
            func.coalesce(func.sum(Payment.amount), 0),
        )
        .where(Payment.direction == PaymentDirection.payment)
        .group_by(Payment.category)
    ).all()
    result = [
        {"category": cat or "سایر", "amount": float(amount)} for cat, amount in rows
    ]
    result.sort(key=lambda r: r["amount"], reverse=True)
    return result


# --- payments & receipts (پرداخت / دریافت) --------------------------------

def invoice_paid(db: Session, invoice_id: int) -> float:
    """Sum of receipts recorded against one sales invoice."""
    return float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.direction == PaymentDirection.receipt,
                Payment.invoice_id == invoice_id,
            )
        )
        or 0
    )


def purchase_paid(db: Session, purchase_id: int) -> float:
    """Sum of payments recorded against one purchase."""
    return float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.direction == PaymentDirection.payment,
                Payment.purchase_id == purchase_id,
            )
        )
        or 0
    )


def recompute_invoice_status(db: Session, invoice: Invoice) -> None:
    """Derive a sales invoice's status from how much has been received."""
    total = float(invoice.total_amount)
    paid = invoice_paid(db, invoice.id)
    if paid <= 0:
        invoice.status = InvoiceStatus.unpaid
    elif paid < total:
        invoice.status = InvoiceStatus.partial
    else:
        invoice.status = InvoiceStatus.paid


def recompute_purchase_status(db: Session, purchase: Purchase) -> None:
    """Derive a purchase's status from how much has been paid."""
    total = float(purchase.total_amount)
    paid = purchase_paid(db, purchase.id)
    if paid <= 0:
        purchase.status = PurchaseStatus.unpaid
    elif paid < total:
        # purchases have no explicit partial state; keep them unpaid until settled
        purchase.status = PurchaseStatus.unpaid
    else:
        purchase.status = PurchaseStatus.paid


def record_payment(
    db: Session,
    *,
    direction: PaymentDirection,
    amount: float,
    paid_at: date | None,
    method: PaymentMethod = PaymentMethod.cash,
    category: str | None = None,
    account_id: int | None = None,
    invoice_id: int | None,
    purchase_id: int | None,
    party_id: int | None,
    recorder_id: int | None,
    note: str | None,
) -> Payment:
    """Record a real cash movement, then refresh the linked doc's status."""
    payment = Payment(
        direction=direction,
        amount=amount,
        paid_at=paid_at,
        method=method,
        category=category,
        account_id=account_id,
        invoice_id=invoice_id,
        purchase_id=purchase_id,
        party_id=party_id,
        recorder_id=recorder_id,
        note=note,
    )
    db.add(payment)
    db.flush()

    if invoice_id is not None:
        inv = db.get(Invoice, invoice_id)
        if inv is not None:
            recompute_invoice_status(db, inv)
    if purchase_id is not None:
        pur = db.get(Purchase, purchase_id)
        if pur is not None:
            recompute_purchase_status(db, pur)
    return payment
