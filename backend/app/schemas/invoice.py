"""Invoice schemas — proforma (پیش‌فاکتور) and final sales invoice.

Each invoice carries its own line items (شرح + تعداد + قیمت واحد). The total is
computed from those lines, never sent by the client.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InvoiceKind, InvoiceStatus


# --- Invoice items ---------------------------------------------------------

class InvoiceItemCreate(BaseModel):
    description: str = Field(min_length=1, max_length=400)  # شرح کالا یا خدمت
    product_model_id: int | None = None  # کالای بدون‌سریال (اختیاری — کسر مقداری)
    stock_item_id: int | None = None  # تک‌کالای سریال‌دار (اختیاری — همان دستگاه)
    quantity: float = Field(default=1, gt=0)  # تعداد / مقدار
    unit_price: float = Field(default=0, ge=0)  # قیمت واحد


class InvoiceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    description: str
    product_model_id: int | None
    stock_item_id: int | None
    quantity: float
    unit_price: float
    line_total: float
    created_at: datetime


# --- Invoices --------------------------------------------------------------

class InvoiceCreate(BaseModel):
    activity_id: int
    kind: InvoiceKind = InvoiceKind.proforma
    settlement_due_date: date | None = None  # تاریخ تصفیه حساب
    source_proforma_id: int | None = None  # اگر از روی یک پیش‌فاکتور ساخته می‌شود
    items: list[InvoiceItemCreate] = Field(default_factory=list)


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus | None = None
    settlement_due_date: date | None = None


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: int
    issuer_id: int
    kind: InvoiceKind
    total_amount: float
    status: InvoiceStatus
    settlement_due_date: date | None
    source_proforma_id: int | None
    created_at: datetime
    items: list[InvoiceItemOut] = []
