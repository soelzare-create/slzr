"""Purchase models — the buying side, symmetric to the selling side.

Contains:
- Purchase      : خرید — a purchase document from a supplier (mirrors Invoice)
- PurchaseItem  : اقلام خرید — the goods bought, at cost (mirrors InvoiceItem)

Flow (mirrors the sale flow):
    choose supplier → record purchase
        → inventory gets a message "add stock" (inbound movement / new unit items)
        → accounting gets a message "record this expense" (خرج)

Rule: like invoicing, the purchase module records the document and its lines; it
does not itself mutate inventory or the ledger — those react to it.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PurchaseStatus
from app.models.mixins import TimestampMixin


class Purchase(Base, TimestampMixin):
    """خرید (سند خرید از تأمین‌کننده)."""

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id"), nullable=False, index=True
    )  # تأمین‌کننده (طرف‌حساب)
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # کاربری که خرید را ثبت کرده
    reference: Mapped[str | None] = mapped_column(String(120))  # شماره سند/فاکتور فروشنده
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # مبلغ کل
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus, native_enum=False, length=20),
        default=PurchaseStatus.unpaid,
        nullable=False,
    )  # وضعیت پرداخت
    settlement_due_date: Mapped[date | None] = mapped_column(
        Date
    )  # تاریخ تصفیه حساب با تأمین‌کننده (هنگام ثبت سند خرید درج می‌شود)

    items: Mapped[list["PurchaseItem"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Purchase {self.id} amount={self.total_amount} {self.status.value}>"


class PurchaseItem(Base, TimestampMixin):
    """اقلام خرید — کالای خریداری‌شده با بهای تمام‌شده."""

    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id"), nullable=False, index=True
    )  # خرید
    # A line is either one serialized stock item OR a quantity of a bulk model.
    stock_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_items.id")
    )  # تک‌کالای سریال‌دار دریافتی
    product_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_models.id")
    )  # مدل کالای بدون‌سریال
    quantity: Mapped[float | None] = mapped_column(Numeric(14, 2))  # مقدار (بدون‌سریال)
    unit_cost: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False
    )  # بهای تمام‌شدهٔ این قلم

    purchase: Mapped["Purchase"] = relationship(back_populates="items")
