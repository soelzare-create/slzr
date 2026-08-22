"""Inventory models — bounded context: warehouse.

A single stock table holds ALL goods:
- ProductModel : مدل کالا — a catalog entry, serial-tracked or not, with a unit
  of measure (واحد شمارش: عدد/متر/…).
- StockItem    : یک ردیف انبار. For serial goods it is one physical unit
  (serial_number set, quantity 1) whose lifecycle is tracked by `status`. For
  non-serial goods it is one in/out movement (`direction` set, `quantity` in the
  model's unit of measure) — so the full in/out history is preserved.

Current stock is computed, never stored:
- serial model     -> number of units whose status is `warehouse`
- non-serial model -> sum(in quantities) − sum(out quantities)

Rule (blueprint): inventory only raises/lowers stock; pricing is not its job.
"""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import MovementDirection, TrackingType, UnitItemStatus
from app.database import Base
from app.models.mixins import TimestampMixin


class ProductModel(Base, TimestampMixin):
    """مدل کالا."""

    __tablename__ = "product_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)  # نام مدل
    part_number: Mapped[str | None] = mapped_column(
        String(120), index=True
    )  # پارت‌نامبر (کد کالای سازنده)
    tracking_type: Mapped[TrackingType] = mapped_column(
        Enum(TrackingType, native_enum=False, length=20), nullable=False
    )  # سریال‌دار یا بدون سریال
    unit_of_measure: Mapped[str] = mapped_column(
        String(30), default="عدد", nullable=False
    )  # واحد شمارش: عدد، متر، کیلوگرم، …
    base_price: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # قیمت پایه
    specs: Mapped[str | None] = mapped_column(String(2000))  # مشخصات فنی

    stock_items: Mapped[list["StockItem"]] = relationship(back_populates="model")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProductModel {self.id} {self.name} ({self.tracking_type.value})>"


class StockItem(Base, TimestampMixin):
    """ردیف انبار — یا تک‌کالای سریال‌دار، یا یک حرکت کالای بدون‌سریال."""

    __tablename__ = "stock_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("product_models.id"), nullable=False, index=True
    )  # مدل کالا
    serial_number: Mapped[str | None] = mapped_column(
        String(120), unique=True, index=True
    )  # شماره سریال (فقط کالای سریال‌دار)
    quantity: Mapped[float] = mapped_column(
        Numeric(14, 2), default=1, nullable=False
    )  # مقدار (سریال‌دار = ۱؛ بدون‌سریال = مقدار حرکت به واحد شمارش)

    # Serial goods use `status`; non-serial goods use `direction`.
    status: Mapped[UnitItemStatus | None] = mapped_column(
        Enum(UnitItemStatus, native_enum=False, length=20)
    )  # وضعیت تک‌کالا: انبار/فروخته/نصب‌شده/خراب
    direction: Mapped[MovementDirection | None] = mapped_column(
        Enum(MovementDirection, native_enum=False, length=10)
    )  # جهت حرکت کالای بدون‌سریال: ورود/خروج

    model: Mapped["ProductModel"] = relationship(back_populates="stock_items")

    def __repr__(self) -> str:  # pragma: no cover
        if self.serial_number:
            return f"<StockItem {self.id} sn={self.serial_number} {self.status}>"
        return f"<StockItem {self.id} {self.direction} qty={self.quantity}>"
