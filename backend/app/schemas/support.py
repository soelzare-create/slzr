"""Ticket schemas — support & ticketing (فاز ۶).

A ticket belongs to a customer and may be tied to a specific device (a
serialized stock unit the customer owns).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketStatus


class TicketCreate(BaseModel):
    customer_id: int
    device_unit_id: int | None = None  # سریال دستگاه (تک‌کالای سریال‌دار)
    owner_id: int | None = None  # مسئول پیگیری
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    owner_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    device_unit_id: int | None
    owner_id: int | None
    title: str
    description: str | None
    status: TicketStatus
    created_at: datetime
