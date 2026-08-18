"""Inventory routes — bounded context: warehouse.

Covers three tables:
- product_models      : the catalog (serial-tracked or quantity-tracked)
- unit_items          : one physical serialized unit
- inventory_movements : in/out movements for quantity (bulk) models

Access model:
- Read  : any authenticated user.
- Write : manager or warehouse.

Rules (blueprint): inventory only raises/lowers stock; pricing is not its job.
Serialized units belong only to serial models; bulk movements only to quantity
models. Current stock is *computed*, never stored:
- serial model  -> number of units whose status is `warehouse` (on hand)
- quantity model -> sum(in) − sum(out)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import (
    MovementDirection,
    TrackingType,
    UnitItemStatus,
    UserRole,
)
from app.models.inventory import InventoryMovement, ProductModel, UnitItem
from app.schemas.inventory import (
    InventoryMovementCreate,
    InventoryMovementOut,
    ProductModelCreate,
    ProductModelOut,
    ProductModelUpdate,
    UnitItemCreate,
    UnitItemOut,
    UnitItemUpdate,
)

router = APIRouter(tags=["inventory"])

can_write = require_roles(UserRole.manager, UserRole.warehouse)


# --- stock helpers ---------------------------------------------------------

def _serial_stock(db: Session, model_id: int | None = None) -> dict[int, float]:
    stmt = (
        select(UnitItem.model_id, func.count())
        .where(UnitItem.status == UnitItemStatus.warehouse)
        .group_by(UnitItem.model_id)
    )
    if model_id is not None:
        stmt = stmt.where(UnitItem.model_id == model_id)
    return {mid: float(n) for mid, n in db.execute(stmt)}


def _bulk_stock(db: Session, model_id: int | None = None) -> dict[int, float]:
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


def _stock_for(db: Session, model: ProductModel) -> float:
    if model.tracking_type == TrackingType.serial:
        return _serial_stock(db, model.id).get(model.id, 0.0)
    return _bulk_stock(db, model.id).get(model.id, 0.0)


def _to_out(model: ProductModel, stock: float) -> ProductModelOut:
    return ProductModelOut.model_validate(
        {**model.__dict__, "current_stock": stock}
    )


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


# --- serialized units ------------------------------------------------------

@router.get(
    "/api/unit-items",
    response_model=list[UnitItemOut],
    dependencies=[Depends(get_current_user)],
)
def list_unit_items(
    db: Session = Depends(get_db),
    model_id: int | None = None,
    status_: UnitItemStatus | None = Query(default=None, alias="status"),
) -> list[UnitItem]:
    stmt = select(UnitItem).order_by(UnitItem.id.desc())
    if model_id is not None:
        stmt = stmt.where(UnitItem.model_id == model_id)
    if status_ is not None:
        stmt = stmt.where(UnitItem.status == status_)
    return list(db.scalars(stmt))


@router.post(
    "/api/unit-items",
    response_model=UnitItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_unit_item(payload: UnitItemCreate, db: Session = Depends(get_db)) -> UnitItem:
    model = db.get(ProductModel, payload.model_id)
    if model is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "مدل کالا معتبر نیست")
    if model.tracking_type != TrackingType.serial:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "تک‌کالا فقط برای مدل کالای سریال‌دار قابل ثبت است",
        )
    exists = db.scalar(
        select(UnitItem).where(UnitItem.serial_number == payload.serial_number)
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "این شماره سریال قبلاً ثبت شده است")

    unit = UnitItem(**payload.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.patch(
    "/api/unit-items/{unit_id}",
    response_model=UnitItemOut,
    dependencies=[Depends(can_write)],
)
def update_unit_item(
    unit_id: int, payload: UnitItemUpdate, db: Session = Depends(get_db)
) -> UnitItem:
    unit = db.get(UnitItem, unit_id)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "تک‌کالا یافت نشد")
    unit.status = payload.status
    db.commit()
    db.refresh(unit)
    return unit


# --- bulk movements --------------------------------------------------------

@router.get(
    "/api/inventory-movements",
    response_model=list[InventoryMovementOut],
    dependencies=[Depends(get_current_user)],
)
def list_movements(
    db: Session = Depends(get_db), model_id: int | None = None
) -> list[InventoryMovement]:
    stmt = select(InventoryMovement).order_by(InventoryMovement.id.desc())
    if model_id is not None:
        stmt = stmt.where(InventoryMovement.model_id == model_id)
    return list(db.scalars(stmt))


@router.post(
    "/api/inventory-movements",
    response_model=InventoryMovementOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_movement(
    payload: InventoryMovementCreate, db: Session = Depends(get_db)
) -> InventoryMovement:
    model = db.get(ProductModel, payload.model_id)
    if model is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "مدل کالا معتبر نیست")
    if model.tracking_type != TrackingType.quantity:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "حرکت انبار فقط برای مدل کالای مقداری قابل ثبت است",
        )
    # Prevent stock from going negative on an outbound movement.
    if payload.direction == MovementDirection.out:
        current = _bulk_stock(db, model.id).get(model.id, 0.0)
        if payload.quantity > current:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"موجودی کافی نیست (موجودی فعلی: {current})",
            )

    movement = InventoryMovement(**payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
