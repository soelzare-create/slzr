"""Invoice model — bounded context: invoicing.

Rule (blueprint): invoicing issues invoices. It never decrements stock itself —
it sends a message ("decrement one") to inventory and a message ("record this
amount") to accounting. The issuer is stored for commission calculation.
"""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import InvoiceStatus
from app.models.mixins import TimestampMixin


class Invoice(Base, TimestampMixin):
    """فاکتورها."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), nullable=False, index=True
    )  # فعالیت
    issuer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # صادرکننده (برای پورسانت)
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # مبلغ کل
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, native_enum=False, length=20),
        default=InvoiceStatus.unpaid,
        nullable=False,
    )  # وضعیت

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Invoice {self.id} amount={self.total_amount} {self.status.value}>"
