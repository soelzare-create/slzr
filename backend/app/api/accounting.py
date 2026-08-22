"""Accounting routes — the ledger, per-party balances, and totals (فاز ۵).

Bounded context: accounting only reports financial events. Entries are created
by the sales and purchase modules (income / expense); here we read them back and
compute one net balance per party.

Access model:
- Read : manager or accountant (financial data). Other roles use the operational
  pages (invoices, purchases) instead.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models.accounting import FinancialDocument, Payment
from app.models.enums import FinancialType, PaymentDirection, UserRole
from app.models.invoice import Invoice
from app.models.purchase import Purchase
from app.models.user import User
from app.schemas.accounting import (
    AccountingSummaryOut,
    FinancialDocumentOut,
    PartyBalanceOut,
    PaymentCreate,
    PaymentOut,
)
from app.services import accounting_service

router = APIRouter(prefix="/api/accounting", tags=["accounting"])

can_read = require_roles(UserRole.manager, UserRole.accountant)
can_write = require_roles(UserRole.manager, UserRole.accountant)


@router.get(
    "/documents",
    response_model=list[FinancialDocumentOut],
    dependencies=[Depends(can_read)],
)
def list_documents(
    db: Session = Depends(get_db),
    party_id: int | None = None,
    type_: FinancialType | None = Query(default=None, alias="type"),
) -> list[FinancialDocument]:
    stmt = select(FinancialDocument).order_by(FinancialDocument.id.desc())
    if party_id is not None:
        stmt = stmt.where(FinancialDocument.party_id == party_id)
    if type_ is not None:
        stmt = stmt.where(FinancialDocument.type == type_)
    return list(db.scalars(stmt))


@router.get(
    "/balances",
    response_model=list[PartyBalanceOut],
    dependencies=[Depends(can_read)],
)
def list_balances(db: Session = Depends(get_db)) -> list[dict]:
    return accounting_service.all_party_balances(db)


@router.get(
    "/summary",
    response_model=AccountingSummaryOut,
    dependencies=[Depends(can_read)],
)
def get_summary(db: Session = Depends(get_db)) -> dict:
    return accounting_service.summary(db)


@router.get(
    "/parties/{party_id}/balance",
    response_model=PartyBalanceOut,
    dependencies=[Depends(can_read)],
)
def get_party_balance(party_id: int, db: Session = Depends(get_db)) -> dict:
    return accounting_service.party_balance(db, party_id)


# --- payments & receipts (پرداخت / دریافت) --------------------------------

@router.get(
    "/payments",
    response_model=list[PaymentOut],
    dependencies=[Depends(can_read)],
)
def list_payments(
    db: Session = Depends(get_db),
    invoice_id: int | None = None,
    purchase_id: int | None = None,
    direction: PaymentDirection | None = None,
) -> list[Payment]:
    stmt = select(Payment).order_by(Payment.id.desc())
    if invoice_id is not None:
        stmt = stmt.where(Payment.invoice_id == invoice_id)
    if purchase_id is not None:
        stmt = stmt.where(Payment.purchase_id == purchase_id)
    if direction is not None:
        stmt = stmt.where(Payment.direction == direction)
    return list(db.scalars(stmt))


@router.post(
    "/payments",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    recorder: User = Depends(can_write),
) -> Payment:
    party_id = payload.party_id
    # A receipt is against a sales invoice; a payment is against a purchase.
    if payload.direction == PaymentDirection.receipt:
        if payload.invoice_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "برای دریافت، فاکتور لازم است")
        invoice = db.get(Invoice, payload.invoice_id)
        if invoice is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "فاکتور معتبر نیست")
        remaining = float(invoice.total_amount) - accounting_service.invoice_paid(
            db, invoice.id
        )
        if payload.amount > remaining + 1e-6:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"مبلغ دریافت از باقی‌ماندهٔ فاکتور ({remaining:g}) بیشتر است",
            )
        if party_id is None:
            party_id = _customer_of(db, invoice)
    else:  # payment
        if payload.purchase_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "برای پرداخت، سند خرید لازم است")
        purchase = db.get(Purchase, payload.purchase_id)
        if purchase is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "سند خرید معتبر نیست")
        if party_id is None:
            party_id = purchase.supplier_id

    payment = accounting_service.record_payment(
        db,
        direction=payload.direction,
        amount=payload.amount,
        paid_at=payload.paid_at,
        invoice_id=payload.invoice_id,
        purchase_id=payload.purchase_id,
        party_id=party_id,
        recorder_id=recorder.id,
        note=payload.note,
    )
    db.commit()
    db.refresh(payment)
    return payment


def _customer_of(db: Session, invoice: Invoice) -> int | None:
    from app.models.activity import Activity

    activity = db.get(Activity, invoice.activity_id)
    return activity.customer_id if activity else None
