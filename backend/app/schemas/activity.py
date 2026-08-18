"""Activity & project-stage schemas (core bounded context)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from pydantic import model_validator

from app.models.enums import ActivityStatus, ActivityType, ProjectStage


# --- Activity items (sales lines) -----------------------------------------

class ActivityItemCreate(BaseModel):
    # A line is either one serialized stock item OR a quantity of a non-serial model.
    stock_item_id: int | None = None
    product_model_id: int | None = None
    quantity: float | None = Field(default=None, gt=0)
    price: float = Field(ge=0)

    @model_validator(mode="after")
    def one_kind_of_good(self) -> "ActivityItemCreate":
        has_serial = self.stock_item_id is not None
        has_bulk = self.product_model_id is not None
        if has_serial == has_bulk:
            raise ValueError("هر قلم باید یا تک‌کالای سریال‌دار باشد یا مدل کالای بدون‌سریال")
        if has_bulk and not self.quantity:
            raise ValueError("برای کالای بدون‌سریال، مقدار لازم است")
        return self


class ActivityItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: int
    stock_item_id: int | None
    product_model_id: int | None
    quantity: float | None
    price: float
    created_at: datetime


# --- Project stages --------------------------------------------------------

class ProjectStageCreate(BaseModel):
    stage: ProjectStage
    entered_at: date | None = None


class ProjectStageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: int
    stage: ProjectStage
    entered_at: date | None
    created_at: datetime


# --- Activities ------------------------------------------------------------

class ActivityBase(BaseModel):
    customer_id: int
    owner_id: int
    type: ActivityType
    title: str | None = Field(default=None, max_length=300)


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    owner_id: int | None = None
    status: ActivityStatus | None = None
    title: str | None = Field(default=None, max_length=300)


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    owner_id: int
    type: ActivityType
    status: ActivityStatus
    title: str | None
    created_at: datetime


class ActivityDetail(ActivityOut):
    """Activity plus its project stages (for the detail view)."""

    stages: list[ProjectStageOut] = []
