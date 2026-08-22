"""Invoice routes — proforma (پیش‌فاکتور) and final sales invoice.

Access model:
- Read  : any authenticated user.
- Write : manager or sales.

Model:
- An activity is only a grouping folder; every priced line lives on the invoice.
- One activity may carry several proformas AND several final invoices.
- A **proforma** is a quote: it has line items but no effect on stock or ledger,
  and it can be edited/deleted freely.
- A **final** invoice, on creation, messages inventory ("take these out of
  stock", only for lines linked to a warehouse product) and accounting ("record
  this income"). It is immutable afterwards except for its payment status.
- Converting a proforma is done by creating a final invoice from its (possibly
  edited) lines, carrying `source_proforma_id` for traceability.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.activity import Activity
from app.models.enums import (
    InvoiceKind,
    InvoiceStatus,
    TrackingType,
    UnitItemStatus,
    UserRole,
)
from app.models.inventory import ProductModel, StockItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceStatusUpdate
from app.services import accounting_service, inventory_service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

can_write = require_roles(UserRole.manager, UserRole.sales)


def _items_total(items: list[InvoiceItem]) -> Decimal:
    return sum(
        (Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) for i in items),
        Decimal("0"),
    )


def _apply_effects(db: Session, invoice: Invoice, activity: Activity) -> None:
    """When a sale becomes final: consume stock (linked lines) and book income."""
    for it in invoice.items:
        if it.stock_item_id is not None:
            inventory_service.consume_item(
                db,
                stock_item_id=it.stock_item_id,
                product_model_id=None,
                quantity=None,
            )
        elif it.product_model_id is not None:
            inventory_service.consume_item(
                db,
                stock_item_id=None,
                product_model_id=it.product_model_id,
                quantity=float(it.quantity),
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


@router.get(
    "/{invoice_id}", response_model=InvoiceOut, dependencies=[Depends(get_current_user)]
)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "فاکتور یافت نشد")
    return invoice


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    issuer: User = Depends(can_write),
) -> Invoice:
    activity = db.get(Activity, payload.activity_id)
    if activity is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "فعالیت معتبر نیست")

    if payload.kind == InvoiceKind.final and not payload.items:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "فاکتور نهایی باید حداقل یک قلم داشته باشد"
        )

    # Validate any warehouse links up front. A line may link to a non-serial
    # product (quantity) OR to a specific serial unit — not both.
    for line in payload.items:
        if line.product_model_id is not None and line.stock_item_id is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "هر ردیف یا کالای بدون‌سریال است یا تک‌کالای سریال‌دار، نه هر دو",
            )
        if line.product_model_id is not None:
            model = db.get(ProductModel, line.product_model_id)
            if model is None:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "کالای انتخاب‌شده معتبر نیست"
                )
            if model.tracking_type != TrackingType.quantity:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "برای کالای سریال‌دار باید یک تک‌کالای مشخص انتخاب شود",
                )
        if line.stock_item_id is not None:
            unit = db.get(StockItem, line.stock_item_id)
            if unit is None or unit.serial_number is None:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "تک‌کالای انتخاب‌شده معتبر نیست"
                )
            # For a FINAL invoice the unit must still be in the warehouse.
            if payload.kind == InvoiceKind.final and unit.status != UnitItemStatus.warehouse:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"تک‌کالای «{unit.serial_number}» در انبار موجود نیست",
                )

    if payload.source_proforma_id is not None:
        src = db.get(Invoice, payload.source_proforma_id)
        if src is None or src.kind != InvoiceKind.proforma:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "پیش‌فاکتور مبدأ معتبر نیست"
            )

    invoice = Invoice(
        activity_id=activity.id,
        issuer_id=issuer.id,
        kind=payload.kind,
        status=InvoiceStatus.unpaid,
        settlement_due_date=payload.settlement_due_date,
        source_proforma_id=payload.source_proforma_id,
    )
    invoice.items = [
        InvoiceItem(
            description=line.description,
            product_model_id=line.product_model_id,
            stock_item_id=line.stock_item_id,
            # a serial unit is always exactly one physical item
            quantity=1 if line.stock_item_id is not None else line.quantity,
            unit_price=line.unit_price,
        )
        for line in payload.items
    ]
    invoice.total_amount = _items_total(invoice.items)

    db.add(invoice)
    db.flush()

    if payload.kind == InvoiceKind.final:
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


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(can_write),
) -> None:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "فاکتور یافت نشد")
    if invoice.kind == InvoiceKind.final:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "فاکتور نهایی قابل حذف نیست (روی انبار و حسابداری اثر گذاشته است)",
        )
    db.delete(invoice)
    db.commit()
