"""Activity & project-stage schemas (core bounded context)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ActivityStatus, ActivityType, ProjectStage


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
