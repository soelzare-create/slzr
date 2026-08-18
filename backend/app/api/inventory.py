"""Inventory routes — bounded context: warehouse.

Over a single stock table:
- product_models : the catalog (serial-tracked or not, with a unit of measure)
- stock_items    : one serialized unit (serial goods) OR one in/out movement
                   (non-serial goods)

Access model:
- Read  : any authenticated user.
- Write : manager or warehouse.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import (
    MovementDirection,
    TrackingType,
    UnitItemStatus,
    UserRole,
)
from app.models.inventory import ProductModel, StockItem
from app.schemas.inventory import (
    ProductModelCreate,
    ProductModelOut,
    ProductModelUpdate,
    StockItemCreate,
    StockItemOut,
    StockItemStatusUpdate,
)
from app.services import inventory_service
from app.services.inventory_service import bulk_stock as _bulk_stock
from app.services.inventory_service import serial_stock as _serial_stock
from app.services.inventory_service import stock_for as _stock_for

router = APIRouter(tags=["inventory"])

can_write = require_roles(UserRole.manager, UserRole.warehouse)


def _to_out(model: ProductModel, stock: float) -> ProductModelOut:
    return ProductModelOut.model_validate({**model.__dict__, "current_stock": stock})


# --- product models --------------------------------------------------------

@router.get(
    "/api/product-models",
    response_model=list[ProductModelOut],
    dependencies=[Depends(get_current_user)],
)
def list_product_models(
    db: Session = Depends(get_db),
    tracking_type: TrackingType | None = None,
    q: str | None = Query(default=None, description="جستجو در نام"),
) -> list[ProductModelOut]:
    stmt = select(ProductModel).order_by(ProductModel.id.desc())
    if tracking_type is not None:
        stmt = stmt.where(ProductModel.tracking_type == tracking_type)
    if q:
        stmt = stmt.where(ProductModel.name.ilike(f"%{q}%"))
    models = list(db.scalars(stmt))

    serial = _serial_stock(db)
    bulk = _bulk_stock(db)
    out = []
    for m in models:
        stock = (
            serial.get(m.id, 0.0)
            if m.tracking_type == TrackingType.serial
            else bulk.get(m.id, 0.0)
        )
        out.append(_to_out(m, stock))
    return out


@router.post(
    "/api/product-models",
    response_model=ProductModelOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_product_model(
    payload: ProductModelCreate, db: Session = Depends(get_db)
) -> ProductModelOut:
    model = ProductModel(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return _to_out(model, 0.0)


@router.get(
    "/api/product-models/{model_id}",
    response_model=ProductModelOut,
    dependencies=[Depends(get_current_user)],
)
def get_product_model(model_id: int, db: Session = Depends(get_db)) -> ProductModelOut:
    model = db.get(ProductModel, model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مدل کالا یافت نشد")
    return _to_out(model, _stock_for(db, model))


@router.patch(
    "/api/product-models/{model_id}",
    response_model=ProductModelOut,
    dependencies=[Depends(can_write)],
)
def update_product_model(
    model_id: int, payload: ProductModelUpdate, db: Session = Depends(get_db)
) -> ProductModelOut:
    model = db.get(ProductModel, model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مدل کالا یافت نشد")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    db.commit()
    db.refresh(model)
    return _to_out(model, _stock_for(db, model))


# --- stock items -----------------------------------------------------------

@router.get(
    "/api/stock-items",
    response_model=list[StockItemOut],
    dependencies=[Depends(get_current_user)],
)
def list_stock_items(
    db: Session = Depends(get_db),
    model_id: int | None = None,
    status_: UnitItemStatus | None = Query(default=None, alias="status"),
) -> list[StockItem]:
    stmt = select(StockItem).order_by(StockItem.id.desc())
    if model_id is not None:
        stmt = stmt.where(StockItem.model_id == model_id)
    if status_ is not None:
        stmt = stmt.where(StockItem.status == status_)
    return list(db.scalars(stmt))


@router.post(
    "/api/stock-items",
    response_model=StockItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_stock_item(
    payload: StockItemCreate, db: Session = Depends(get_db)
) -> StockItem:
    model = db.get(ProductModel, payload.model_id)
    if model is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "مدل کالا معتبر نیست")

    if model.tracking_type == TrackingType.serial:
        if not payload.serial_number:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "برای کالای سریال‌دار، شماره سریال لازم است"
            )
        dup = db.scalar(
            select(StockItem).where(StockItem.serial_number == payload.serial_number)
        )
        if dup:
            raise HTTPException(status.HTTP_409_CONFLICT, "این شماره سریال قبلاً ثبت شده است")
        item = inventory_service.receive_serial(
            db, model_id=model.id, serial_number=payload.serial_number
        )
        db.commit()
        db.refresh(item)
        return item

    # non-serial: needs quantity + direction
    if payload.serial_number:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "این کالا بدون‌سریال است؛ شماره سریال نپذیرید"
        )
    if not payload.quantity or payload.direction is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "برای کالای بدون‌سریال، مقدار و جهت لازم است"
        )
    if payload.direction == MovementDirection.out:
        current = _bulk_stock(db, model.id).get(model.id, 0.0)
        if payload.quantity > current:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"موجودی کافی نیست (موجودی فعلی: {current})"
            )
    item = inventory_service.add_movement(
        db, model_id=model.id, quantity=payload.quantity, direction=payload.direction
    )
    db.commit()
    db.refresh(item)
    return item


@router.patch(
    "/api/stock-items/{item_id}",
    response_model=StockItemOut,
    dependencies=[Depends(can_write)],
)
def update_stock_item_status(
    item_id: int, payload: StockItemStatusUpdate, db: Session = Depends(get_db)
) -> StockItem:
    item = db.get(StockItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ردیف انبار یافت نشد")
    if item.serial_number is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "وضعیت فقط برای کالای سریال‌دار معنا دارد"
        )
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return item
