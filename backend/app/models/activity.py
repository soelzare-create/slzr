"""Activity models — the central table that ties the company's work together.

Contains:
- Activity        : فعالیت‌ها (central) — a project, a sale, or a support contract
- ProjectStage    : مراحل پروژه — stage history, only for project activities
- ActivityItem    : اقلام فعالیت — the goods/lines attached to an activity

Rule (blueprint): the project/activity module drives work forward but does NOT
create financial documents itself.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ActivityStatus, ActivityType, ProjectStage as StageEnum
from app.models.mixins import TimestampMixin


class Activity(Base, TimestampMixin):
    """فعالیت‌ها (جدول مرکزی)."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )  # مشتری
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # مسئول
    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, native_enum=False, length=20), nullable=False
    )  # نوع
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(ActivityStatus, native_enum=False, length=20),
        default=ActivityStatus.open,
        nullable=False,
    )  # وضعیت
    title: Mapped[str | None] = mapped_column(String(300))

    stages: Mapped[list["ProjectStage"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )
    items: Mapped[list["ActivityItem"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Activity {self.id} {self.type.value} status={self.status.value}>"


class ProjectStage(Base, TimestampMixin):
    """مراحل پروژه (فقط برای پروژه‌ها)."""

    __tablename__ = "project_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), nullable=False, index=True
    )  # فعالیت
    stage: Mapped[StageEnum] = mapped_column(
        Enum(StageEnum, native_enum=False, length=20), nullable=False
    )  # مرحله
    entered_at: Mapped[date | None] = mapped_column(Date)  # تاریخ ورود به مرحله

    activity: Mapped["Activity"] = relationship(back_populates="stages")


class ActivityItem(Base, TimestampMixin):
    """اقلام فعالیت — کالاهای متصل به یک فعالیت با قیمت آن قلم."""

    __tablename__ = "activity_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), nullable=False, index=True
    )  # فعالیت
    # A line refers either to one serialized unit item OR to a quantity of a model.
    unit_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("unit_items.id")
    )  # کالای سریال‌دار
    product_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_models.id")
    )  # مدل کالای فله‌ای
    quantity: Mapped[float | None] = mapped_column(Numeric(14, 2))  # مقدار (فله‌ای)
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)  # قیمت این قلم

    activity: Mapped["Activity"] = relationship(back_populates="items")
