"""Inventory schemas — product models and the single stock-item table."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MovementDirection, TrackingType, UnitItemStatus


# --- Product model ---------------------------------------------------------

class ProductModelBase(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    part_number: str | None = Field(default=None, max_length=120)
    tracking_type: TrackingType
    unit_of_measure: str = Field(default="عدد", min_length=1, max_length=30)
    base_price: float = Field(default=0, ge=0)
    specs: str | None = Field(default=None, max_length=2000)


class ProductModelCreate(ProductModelBase):
    pass


class ProductModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    part_number: str | None = Field(default=None, max_length=120)
    unit_of_measure: str | None = Field(default=None, min_length=1, max_length=30)
    base_price: float | None = Field(default=None, ge=0)
    specs: str | None = Field(default=None, max_length=2000)
    # tracking_type is intentionally immutable once stock may exist.


class ProductModelOut(ProductModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    current_stock: float = 0  # in-stock serial units, or net non-serial quantity


# --- Stock item ------------------------------------------------------------

class StockItemCreate(BaseModel):
    """Create a stock row.

    Serial model     -> provide `serial_number` (one unit enters the warehouse).
    Non-serial model -> provide `quantity` + `direction` (one in/out movement).
    """
    model_id: int
    serial_number: str | None = Field(default=None, max_length=120)
    quantity: float | None = Field(default=None, gt=0)
    direction: MovementDirection | None = None


class StockItemStatusUpdate(BaseModel):
    status: UnitItemStatus


class StockItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    serial_number: str | None
    quantity: float
    status: UnitItemStatus | None
    direction: MovementDirection | None
    created_at: datetime
