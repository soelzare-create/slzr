"""Invoice model — bounded context: invoicing.

An activity is only a folder that groups work (a project, a product sale, a
support contract). The priced lines live on the invoice itself, not on the
activity — so one activity can carry several proformas (پیش‌فاکتور) and several
final invoices (فاکتور), each with its own line items priced at the day's rate.

Rule (blueprint): invoicing issues invoices. It never decrements stock itself —
it asks inventory ("take these out") and accounting ("record this income") when
a *final* invoice is issued. A proforma is only a quote and has no such effect.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import InvoiceKind, InvoiceStatus
from app.models.mixins import TimestampMixin


class Invoice(Base, TimestampMixin):
    """فاکتورها — پیش‌فاکتور یا فاکتور نهایی، هر کدام با اقلام خودش."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), nullable=False, index=True
    )  # فعالیت (پوشهٔ دسته‌بندی)
    issuer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # صادرکننده (برای پورسانت)
    kind: Mapped[InvoiceKind] = mapped_column(
        Enum(InvoiceKind, native_enum=False, length=20),
        default=InvoiceKind.final,
        nullable=False,
    )  # پیش‌فاکتور یا فاکتور نهایی
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # مبلغ کل (از جمع اقلام محاسبه می‌شود)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, native_enum=False, length=20),
        default=InvoiceStatus.unpaid,
        nullable=False,
    )  # وضعیت
    settlement_due_date: Mapped[date | None] = mapped_column(
        Date
    )  # تاریخ تصفیه حساب — زمانی که باید حساب تسویه شود
    source_proforma_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), index=True
    )  # اگر این فاکتور از روی یک پیش‌فاکتور ساخته شده، شناسهٔ آن

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Invoice {self.id} {self.kind.value} amount={self.total_amount} {self.status.value}>"


class InvoiceItem(Base, TimestampMixin):
    """اقلام فاکتور — هر ردیف: شرح (کالا یا خدمت) + تعداد + قیمت واحد.

    اتصال به انبار اختیاری است و هنگام صدور فاکتور نهایی موجودی را کم می‌کند:
    - `product_model_id` : کالای بدون‌سریال (مقداری) — به اندازهٔ `quantity` خارج می‌شود.
    - `stock_item_id`    : یک تک‌کالای سریال‌دارِ مشخص — همان دستگاه «فروخته» می‌شود.
    ردیف‌های خدمت/شرح آزاد (بدون اتصال) اثری روی انبار ندارند.
    """

    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"), nullable=False, index=True
    )  # فاکتور
    description: Mapped[str] = mapped_column(
        String(400), nullable=False
    )  # شرح ردیف (نام کالا یا خدمت)
    product_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_models.id")
    )  # کالای بدون‌سریال (اختیاری — برای کسر مقداری موجودی)
    stock_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_items.id")
    )  # تک‌کالای سریال‌دار (اختیاری — همان دستگاه فروخته می‌شود)
    quantity: Mapped[float] = mapped_column(
        Numeric(14, 2), default=1, nullable=False
    )  # تعداد / مقدار
    unit_price: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # قیمت واحد

    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    @property
    def line_total(self) -> float:
        return float(self.quantity) * float(self.unit_price)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<InvoiceItem {self.id} {self.description} {self.quantity}×{self.unit_price}>"
