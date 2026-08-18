"""Invoice schemas — proforma (پیش‌فاکتور) and final sales invoice."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import InvoiceKind, InvoiceStatus


class InvoiceCreate(BaseModel):
    activity_id: int
    kind: InvoiceKind = InvoiceKind.final
    settlement_due_date: date | None = None  # تاریخ تصفیه حساب


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
    created_at: datetime
