"""Inventory service — stock computation and stock adjustments.

This is the only place stock is calculated or changed. Other modules (sales,
purchasing) call these functions rather than touching inventory tables.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.enums import MovementDirection, TrackingType, UnitItemStatus
from app.models.inventory import InventoryMovement, ProductModel, UnitItem


# --- stock computation -----------------------------------------------------

def serial_stock(db: Session, model_id: int | None = None) -> dict[int, float]:
    """In-warehouse unit count per serial model."""
    stmt = (
        select(UnitItem.model_id, func.count())
        .where(UnitItem.status == UnitItemStatus.warehouse)
        .group_by(UnitItem.model_id)
    )
    if model_id is not None:
        stmt = stmt.where(UnitItem.model_id == model_id)
    return {mid: float(n) for mid, n in db.execute(stmt)}


def bulk_stock(db: Session, model_id: int | None = None) -> dict[int, float]:
    """Net quantity (sum of ins minus outs) per quantity model."""
    signed = func.sum(
        case(
            (InventoryMovement.direction == MovementDirection.in_, InventoryMovement.quantity),
            else_=-InventoryMovement.quantity,
        )
    )
    stmt = select(InventoryMovement.model_id, signed).group_by(InventoryMovement.model_id)
    if model_id is not None:
        stmt = stmt.where(InventoryMovement.model_id == model_id)
    return {mid: float(total or 0) for mid, total in db.execute(stmt)}


def stock_for(db: Session, model: ProductModel) -> float:
    if model.tracking_type == TrackingType.serial:
        return serial_stock(db, model.id).get(model.id, 0.0)
    return bulk_stock(db, model.id).get(model.id, 0.0)


# --- stock adjustments -----------------------------------------------------

def consume_item(
    db: Session,
    *,
    unit_item_id: int | None,
    product_model_id: int | None,
    quantity: float | None,
) -> None:
    """Take one line's worth of goods OUT of stock (a sale is being finalized).

    Serial line: mark the specific unit as sold. Bulk line: record an outbound
    movement, guarding against negative stock. Flushes but does not commit.
    """
    if unit_item_id is not None:
        unit = db.get(UnitItem, unit_item_id)
        if unit is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "تک‌کالا یافت نشد")
        if unit.status != UnitItemStatus.warehouse:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"تک‌کالای «{unit.serial_number}» در انبار موجود نیست",
            )
        unit.status = UnitItemStatus.sold
        db.flush()
        return

    if product_model_id is not None and quantity:
        available = bulk_stock(db, product_model_id).get(product_model_id, 0.0)
        if quantity > available:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"موجودی کافی نیست (موجودی فعلی: {available})",
            )
        db.add(
            InventoryMovement(
                model_id=product_model_id,
                quantity=quantity,
                direction=MovementDirection.out,
            )
        )
        db.flush()
        return

    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY, "قلم فاقد کالای معتبر است"
    )
