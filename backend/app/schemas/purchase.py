"""Purchase schemas — recording a purchase from a supplier (سمت خرید).

Mirror of the sales side: a purchase carries lines (اقلام خرید) at cost. When
recorded it brings goods into stock and books an expense (خرج).
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PurchaseStatus


class PurchaseItemCreate(BaseModel):
    """One purchased line.

    - Existing warehouse product: give `product_model_id` (+ `serial_number` for
      a serial model, or `quantity` for a bulk one) — the goods enter stock.
    - Free item / service: give `description` (no product link) — it is
      auto-registered as a catalog service and does NOT affect stock.
    """

    product_model_id: int | None = None
    description: str | None = Field(default=None, max_length=400)
    serial_number: str | None = Field(default=None, max_length=120)
    quantity: float | None = Field(default=None, gt=0)
    unit_cost: float = Field(ge=0)  # بهای تمام‌شدهٔ هر واحد


class PurchaseItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_id: int
    description: str | None
    stock_item_id: int | None
    product_model_id: int | None
    quantity: float | None
    unit_cost: float


class PurchaseCreate(BaseModel):
    supplier_id: int
    reference: str | None = Field(default=None, max_length=120)  # شماره سند فروشنده
    settlement_due_date: date | None = None  # تاریخ تصفیه با تأمین‌کننده
    items: list[PurchaseItemCreate] = Field(min_length=1)


class PurchaseStatusUpdate(BaseModel):
    status: PurchaseStatus | None = None
    settlement_due_date: date | None = None


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    buyer_id: int
    reference: str | None
    total_amount: float
    status: PurchaseStatus
    settlement_due_date: date | None
    created_at: datetime
    items: list[PurchaseItemOut] = []
