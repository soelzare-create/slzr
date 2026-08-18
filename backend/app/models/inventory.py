"""Inventory models — bounded context: warehouse.

Contains:
- ProductModel      : مدل کالا — a catalog entry (a type of product)
- UnitItem          : تک‌کالا — one physical, serialized unit of a serial model
- InventoryMovement : حرکت انبار — in/out movements for quantity (bulk) models

Rule (blueprint): inventory only increases/decreases stock. Pricing is not its
job, and it never decrements itself — it acts on a message from the invoice
module.
"""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import MovementDirection, TrackingType, UnitItemStatus
from app.models.mixins import TimestampMixin


class ProductModel(Base, TimestampMixin):
    """مدل کالا."""

    __tablename__ = "product_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)  # نام مدل
    tracking_type: Mapped[TrackingType] = mapped_column(
        Enum(TrackingType, native_enum=False, length=20), nullable=False
    )  # نوع ردیابی: سریال‌دار یا مقداری
    base_price: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, nullable=False
    )  # قیمت پایه
    specs: Mapped[str | None] = mapped_column(String(2000))  # مشخصات فنی

    units: Mapped[list["UnitItem"]] = relationship(back_populates="model")
    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="model"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProductModel {self.id} {self.name} ({self.tracking_type.value})>"


class UnitItem(Base, TimestampMixin):
    """تک‌کالا (کالای سریال‌دار)."""

    __tablename__ = "unit_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("product_models.id"), nullable=False, index=True
    )  # مدل
    serial_number: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )  # شماره سریال یکتا
    status: Mapped[UnitItemStatus] = mapped_column(
        Enum(UnitItemStatus, native_enum=False, length=20),
        default=UnitItemStatus.warehouse,
        nullable=False,
    )  # وضعیت

    model: Mapped["ProductModel"] = relationship(back_populates="units")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UnitItem {self.id} sn={self.serial_number} {self.status.value}>"


class InventoryMovement(Base, TimestampMixin):
    """حرکت انبار (کالای مقداری/فله‌ای)."""

    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("product_models.id"), nullable=False, index=True
    )  # مدل
    quantity: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # مقدار
    direction: Mapped[MovementDirection] = mapped_column(
        Enum(MovementDirection, native_enum=False, length=10), nullable=False
    )  # جهت: ورود/خروج

    model: Mapped["ProductModel"] = relationship(back_populates="movements")
