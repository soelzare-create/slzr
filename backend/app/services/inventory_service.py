"""Inventory service — stock computation and stock adjustments.

The only place stock is calculated or changed, over the single `stock_items`
table. Serial rows carry a `status`; non-serial rows carry a `direction`.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.enums import MovementDirection, TrackingType, UnitItemStatus
from app.models.inventory import ProductModel, StockItem


# --- stock computation -----------------------------------------------------

def serial_stock(db: Session, model_id: int | None = None) -> dict[int, float]:
    """In-warehouse unit count per serial model (rows with status=warehouse)."""
    stmt = (
        select(StockItem.model_id, func.coalesce(func.sum(StockItem.quantity), 0))
        .where(StockItem.status == UnitItemStatus.warehouse)
        .group_by(StockItem.model_id)
    )
    if model_id is not None:
        stmt = stmt.where(StockItem.model_id == model_id)
    return {mid: float(n) for mid, n in db.execute(stmt)}


def bulk_stock(db: Session, model_id: int | None = None) -> dict[int, float]:
    """Net quantity (ins minus outs) per non-serial model."""
    signed = func.sum(
        case(
            (StockItem.direction == MovementDirection.in_, StockItem.quantity),
            else_=-StockItem.quantity,
        )
    )
    stmt = (
        select(StockItem.model_id, signed)
        .where(StockItem.direction.is_not(None))
        .group_by(StockItem.model_id)
    )
    if model_id is not None:
        stmt = stmt.where(StockItem.model_id == model_id)
    return {mid: float(total or 0) for mid, total in db.execute(stmt)}


def stock_for(db: Session, model: ProductModel) -> float:
    if model.is_service:
        return 0.0  # services are not stocked
    if model.tracking_type == TrackingType.serial:
        return serial_stock(db, model.id).get(model.id, 0.0)
    return bulk_stock(db, model.id).get(model.id, 0.0)


def ensure_product(
    db: Session,
    *,
    name: str,
    is_service: bool = True,
    unit_price: float = 0.0,
) -> ProductModel:
    """Find a catalog entry by name, or create one. Used to auto-register a
    free-text good/service typed on an invoice or purchase line so it is kept
    for reuse. New auto-entries default to a (non-stocked) service."""
    name = (name or "").strip()
    existing = db.scalar(
        select(ProductModel).where(func.lower(ProductModel.name) == name.lower())
    )
    if existing is not None:
        return existing
    model = ProductModel(
        name=name,
        tracking_type=TrackingType.quantity,
        is_service=is_service,
        unit_of_measure="خدمت" if is_service else "عدد",
        base_price=unit_price,
    )
    db.add(model)
    db.flush()
    return model


# --- stock adjustments -----------------------------------------------------

def consume_item(
    db: Session,
    *,
    stock_item_id: int | None,
    product_model_id: int | None,
    quantity: float | None,
) -> None:
    """Take one sale line's worth of goods OUT of stock.

    Serial line: mark the specific unit sold. Non-serial line: append an outbound
    movement, guarding against negative stock. Flushes but does not commit.
    """
    if stock_item_id is not None:
        unit = db.get(StockItem, stock_item_id)
        if unit is None or unit.serial_number is None:
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
            StockItem(
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


def receive_item(
    db: Session,
    *,
    model_id: int,
    serial_number: str | None,
    quantity: float | None,
) -> StockItem:
    """Bring one purchase line's worth of goods INTO stock (mirror of consume_item).

    Serial model: register the received unit by its serial. Non-serial model:
    append an inbound movement. Validates against the model's tracking type.
    Flushes but does not commit.
    """
    model = db.get(ProductModel, model_id)
    if model is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "مدل کالا معتبر نیست")

    if model.tracking_type == TrackingType.serial:
        if not serial_number:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "برای کالای سریال‌دار، شماره سریال لازم است"
            )
        dup = db.scalar(
            select(StockItem).where(StockItem.serial_number == serial_number)
        )
        if dup:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "این شماره سریال قبلاً ثبت شده است"
            )
        return receive_serial(db, model_id=model_id, serial_number=serial_number)

    # non-serial: needs a quantity (no serial number)
    if serial_number:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "این کالا بدون‌سریال است؛ شماره سریال نپذیرید"
        )
    if not quantity:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "برای کالای بدون‌سریال، مقدار لازم است"
        )
    return add_movement(
        db, model_id=model_id, quantity=quantity, direction=MovementDirection.in_
    )


def receive_serial(db: Session, *, model_id: int, serial_number: str) -> StockItem:
    """Add one serialized unit into the warehouse."""
    item = StockItem(
        model_id=model_id,
        serial_number=serial_number,
        quantity=1,
        status=UnitItemStatus.warehouse,
    )
    db.add(item)
    db.flush()
    return item


def add_movement(
    db: Session, *, model_id: int, quantity: float, direction: MovementDirection
) -> StockItem:
    """Add one in/out movement for a non-serial model."""
    item = StockItem(model_id=model_id, quantity=quantity, direction=direction)
    db.add(item)
    db.flush()
    return item
