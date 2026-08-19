"""Reporting routes — a single management overview (فاز ۷).

Read-only aggregation across the other bounded contexts. Because it surfaces
financials, it is limited to manager or accountant (same as the accounting view).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models.activity import Activity
from app.models.enums import TicketStatus, UserRole
from app.models.inventory import ProductModel
from app.models.invoice import Invoice
from app.models.party import Party
from app.models.purchase import Purchase
from app.models.support import Ticket
from app.schemas.reports import (
    Counts,
    Finance,
    PartyBalanceMini,
    ReportsOverview,
    StatusBreakdown,
)
from app.services import accounting_service

router = APIRouter(prefix="/api/reports", tags=["reports"])

can_read = require_roles(UserRole.manager, UserRole.accountant)


def _count(db: Session, model, *where) -> int:
    stmt = select(func.count()).select_from(model)
    for clause in where:
        stmt = stmt.where(clause)
    return int(db.scalar(stmt) or 0)


def _status_breakdown(db: Session, model) -> StatusBreakdown:
    rows = db.execute(select(model.status, func.count()).group_by(model.status)).all()
    data = {"unpaid": 0, "paid": 0, "overdue": 0}
    total = 0
    for st, cnt in rows:
        data[st.value] = int(cnt)
        total += int(cnt)
    return StatusBreakdown(total=total, **data)


@router.get("/overview", response_model=ReportsOverview, dependencies=[Depends(can_read)])
def overview(db: Session = Depends(get_db)) -> ReportsOverview:
    counts = Counts(
        customers=_count(db, Party, Party.is_customer.is_(True)),
        suppliers=_count(db, Party, Party.is_supplier.is_(True)),
        activities=_count(db, Activity),
        products=_count(db, ProductModel),
        open_tickets=_count(db, Ticket, Ticket.status == TicketStatus.open),
    )
    finance = Finance(**accounting_service.summary(db))

    balances = accounting_service.all_party_balances(db)
    debtors = [b for b in balances if b["balance"] > 0][:5]
    creditors = sorted(
        (b for b in balances if b["balance"] < 0), key=lambda b: b["balance"]
    )[:5]

    return ReportsOverview(
        counts=counts,
        finance=finance,
        invoices=_status_breakdown(db, Invoice),
        purchases=_status_breakdown(db, Purchase),
        top_debtors=[
            PartyBalanceMini(
                party_id=b["party_id"], party_name=b["party_name"], balance=b["balance"]
            )
            for b in debtors
        ],
        top_creditors=[
            PartyBalanceMini(
                party_id=b["party_id"], party_name=b["party_name"], balance=b["balance"]
            )
            for b in creditors
        ],
    )
