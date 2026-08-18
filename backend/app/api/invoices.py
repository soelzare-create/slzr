"""Invoice routes — proforma (پیش‌فاکتور) and final sales invoice.

Access model:
- Read  : any authenticated user.
- Write : manager or sales.

Rules:
- Total is computed from the activity's items (اقلام فعالیت).
- A **proforma** is a quote: no effect on stock or the ledger.
- Finalizing (creating a `final` invoice, or converting a proforma) makes the
  invoice module message inventory ("take these out of stock") and accounting
  ("record this income"). Only one final invoice per activity.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.activity import Activity, ActivityItem
from app.models.enums import InvoiceKind, InvoiceStatus, UserRole
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceStatusUpdate
from app.services import accounting_service, inventory_service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

can_write = require_roles(UserRole.manager, UserRole.sales)


def _activity_total(db: Session, activity_id: int) -> tuple[Decimal, list[ActivityItem]]:
    items = list(
        db.scalars(select(ActivityItem).where(ActivityItem.activity_id == activity_id))
    )
    total = sum((i.price for i in items), Decimal("0"))
    return total, items


def _has_final(db: Session, activity_id: int, exclude_id: int | None = None) -> bool:
    stmt = select(Invoice).where(
        Invoice.activity_id == activity_id, Invoice.kind == InvoiceKind.final
    )
    if exclude_id is not None:
        stmt = stmt.where(Invoice.id != exclude_id)
    return db.scalar(stmt) is not None


def _apply_effects(db: Session, invoice: Invoice, activity: Activity) -> None:
    """Message inventory and accounting when a sale becomes final."""
    items = db.scalars(
        select(ActivityItem).where(ActivityItem.activity_id == activity.id)
    ).all()
    if not items:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "فعالیت هیچ قلمی ندارد؛ فاکتور نهایی ممکن نیست"
        )
    for it in items:
        inventory_service.consume_item(
            db,
            stock_item_id=it.stock_item_id,
            product_model_id=it.product_model_id,
            quantity=float(it.quantity) if it.quantity is not None else None,
        )
    accounting_service.record_income(
        db,
        amount=float(invoice.total_amount),
        party_id=activity.customer_id,
        invoice_id=invoice.id,
    )


@router.get("", response_model=list[InvoiceOut], dependencies=[Depends(get_current_user)])
def list_invoices(
    db: Session = Depends(get_db),
    activity_id: int | None = None,
    kind: InvoiceKind | None = None,
    status_: InvoiceStatus | None = Query(default=None, alias="status"),
) -> list[Invoice]:
    stmt = select(Invoice).order_by(Invoice.id.desc())
    if activity_id is not None:
        stmt = stmt.where(Invoice.activity_id == activity_id)
    if kind is not None:
        stmt = stmt.where(Invoice.kind == kind)
    if status_ is not None:
        stmt = stmt.where(Invoice.status == status_)
    return list(db.scalars(stmt))


@router.post(
    "", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED
)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    issuer: User = Depends(can_write),
) -> Invoice:
    activity = db.get(Activity, payload.activity_id)
    if activity is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "فعالیت معتبر نیست")

    total, _ = _activity_total(db, activity.id)
    invoice = Invoice(
        activity_id=activity.id,
        issuer_id=issuer.id,
        kind=payload.kind,
        total_amount=total,
        status=InvoiceStatus.unpaid,
        settlement_due_date=payload.settlement_due_date,
    )

    if payload.kind == InvoiceKind.final:
        if _has_final(db, activity.id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "برای این فعالیت فاکتور نهایی صادر شده است"
            )
        db.add(invoice)
        db.flush()
        _apply_effects(db, invoice, activity)

    else:  # proforma — no stock/ledger effect
        db.add(invoice)

    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/finalize", response_model=InvoiceOut)
def finalize_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    issuer: User = Depends(can_write),
) -> Invoice:
    """Convert a proforma into a final invoice and apply its effects."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "فاکتور یافت نشد")
    if invoice.kind == InvoiceKind.final:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "این فاکتور نهایی است")
    if _has_final(db, invoice.activity_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "برای این فعالیت فاکتور نهایی صادر شده است"
        )

    activity = db.get(Activity, invoice.activity_id)
    # Recompute the total in case items changed since the proforma was issued.
    total, _ = _activity_total(db, activity.id)
    invoice.total_amount = total
    invoice.kind = InvoiceKind.final
    db.flush()
    _apply_effects(db, invoice, activity)

    db.commit()
    db.refresh(invoice)
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(can_write),
) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "فاکتور یافت نشد")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(invoice, field, value)
    db.commit()
    db.refresh(invoice)
    return invoice
