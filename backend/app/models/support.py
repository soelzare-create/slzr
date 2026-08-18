"""Ticket model — bounded context: support & ticketing.

A ticket is tied to a customer and, optionally, to a specific physical device
(a serialized unit item).
"""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import TicketStatus
from app.models.mixins import TimestampMixin


class Ticket(Base, TimestampMixin):
    """تیکت‌ها (پشتیبانی)."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id"), nullable=False, index=True
    )  # مشتری (طرف‌حساب با نقش مشتری)
    device_unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_items.id"), index=True
    )  # سریال دستگاه (تک‌کالای سریال‌دار)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )  # مسئول پیگیری
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4000))
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, native_enum=False, length=20),
        default=TicketStatus.open,
        nullable=False,
    )  # وضعیت

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Ticket {self.id} {self.status.value}>"
