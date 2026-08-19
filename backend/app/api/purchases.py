"""Purchase routes — recording a purchase from a supplier (فاز ۴B).

Symmetric to the sales/invoice side:
- Total is computed from the purchase lines (بهای تمام‌شده × مقدار).
- Recording a purchase makes the module message inventory ("add these to
  stock") and accounting ("book this expense"). Unlike sales there is no
  proforma stage — a purchase document is real, so effects apply on creation.

Access model:
- Read  : any authenticated user.
- Write : manager or warehouse (the buying side).
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import PurchaseStatus, UserRole
from app.models.party import Party
from app.models.purchase import Purchase, PurchaseItem
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseOut, PurchaseStatusUpdate
from app.services import accounting_service, inventory_service

router = APIRouter(prefix="/api/purchases", tags=["purchases"])

can_write = require_roles(UserRole.manager, UserRole.warehouse)


@router.get("", response_model=list[PurchaseOut], dependencies=[Depends(get_current_user)])
def list_purchases(
    db: Session = Depends(get_db),
    supplier_id: int | None = None,
    status_: PurchaseStatus | None = Query(default=None, alias="status"),
) -> list[Purchase]:
    stmt = select(Purchase).order_by(Purchase.id.desc())
    if supplier_id is not None:
        stmt = stmt.where(Purchase.supplier_id == supplier_id)
    if status_ is not None:
        stmt = stmt.where(Purchase.status == status_)
    return list(db.scalars(stmt))


@router.post("", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
def create_purchase(
    payload: PurchaseCreate,
    db: Session = Depends(get_db),
    buyer: User = Depends(can_write),
) -> Purchase:
    supplier = db.get(Party, payload.supplier_id)
    if supplier is None or not supplier.is_supplier:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "تأمین‌کننده معتبر نیست"
        )

    purchase = Purchase(
        supplier_id=supplier.id,
        buyer_id=buyer.id,
        reference=payload.reference,
        status=PurchaseStatus.unpaid,
        settlement_due_date=payload.settlement_due_date,
        total_amount=Decimal("0"),
    )
    db.add(purchase)
    db.flush()

    total = Decimal("0")
    for line in payload.items:
        # Inventory brings the goods in and tells us what kind of row it created.
        unit = inventory_service.receive_item(
            db,
            model_id=line.product_model_id,
            serial_number=line.serial_number,
            quantity=float(line.quantity) if line.quantity is not None else None,
        )
        unit_cost = Decimal(str(line.unit_cost))
        if unit.serial_number is not None:  # serialized receipt (qty = 1)
            db.add(
                PurchaseItem(
                    purchase_id=purchase.id,
                    stock_item_id=unit.id,
                    unit_cost=line.unit_cost,
                )
            )
            total += unit_cost
        else:  # bulk inbound movement
            db.add(
                PurchaseItem(
                    purchase_id=purchase.id,
                    product_model_id=line.product_model_id,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                )
            )
            total += unit_cost * Decimal(str(line.quantity))

    purchase.total_amount = total
    db.flush()
    accounting_service.record_expense(
        db, amount=float(total), party_id=supplier.id, purchase_id=purchase.id
    )
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get(
    "/{purchase_id}", response_model=PurchaseOut, dependencies=[Depends(get_current_user)]
)
def get_purchase(purchase_id: int, db: Session = Depends(get_db)) -> Purchase:
    purchase = db.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "سند خرید یافت نشد")
    return purchase


@router.patch("/{purchase_id}", response_model=PurchaseOut)
def update_purchase(
    purchase_id: int,
    payload: PurchaseStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(can_write),
) -> Purchase:
    purchase = db.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "سند خرید یافت نشد")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(purchase, field, value)
    db.commit()
    db.refresh(purchase)
    return purchase
