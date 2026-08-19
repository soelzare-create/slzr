"""Accounting routes — the ledger, per-party balances, and totals (فاز ۵).

Bounded context: accounting only reports financial events. Entries are created
by the sales and purchase modules (income / expense); here we read them back and
compute one net balance per party.

Access model:
- Read : manager or accountant (financial data). Other roles use the operational
  pages (invoices, purchases) instead.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models.accounting import FinancialDocument
from app.models.enums import FinancialType, UserRole
from app.schemas.accounting import (
    AccountingSummaryOut,
    FinancialDocumentOut,
    PartyBalanceOut,
)
from app.services import accounting_service

router = APIRouter(prefix="/api/accounting", tags=["accounting"])

can_read = require_roles(UserRole.manager, UserRole.accountant)


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
