"""Inventory schemas — product models, serialized units, and bulk movements."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MovementDirection, TrackingType, UnitItemStatus


# --- Product model ---------------------------------------------------------

class ProductModelBase(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    tracking_type: TrackingType
    base_price: float = Field(default=0, ge=0)
    specs: str | None = Field(default=None, max_length=2000)


class ProductModelCreate(ProductModelBase):
    pass


class ProductModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    base_price: float | None = Field(default=None, ge=0)
    specs: str | None = Field(default=None, max_length=2000)
    # tracking_type is intentionally immutable once units/movements may exist.


class ProductModelOut(ProductModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    current_stock: float = 0  # in-stock serial units, or net bulk quantity


# --- Serialized unit item --------------------------------------------------

class UnitItemCreate(BaseModel):
    model_id: int
    serial_number: str = Field(min_length=1, max_length=120)
    status: UnitItemStatus = UnitItemStatus.warehouse


class UnitItemUpdate(BaseModel):
    status: UnitItemStatus


class UnitItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    serial_number: str
    status: UnitItemStatus
    created_at: datetime


# --- Bulk inventory movement -----------------------------------------------

class InventoryMovementCreate(BaseModel):
    model_id: int
    quantity: float = Field(gt=0)
    direction: MovementDirection


class InventoryMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    quantity: float
    direction: MovementDirection
    created_at: datetime
