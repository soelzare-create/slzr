"""Task schemas — internal referrals (ارجاعات).

A task is referred from one employee (creator) to another (assignee), tracked
through assigned → in_progress → done. `scheduled_at` holds the planned time
(e.g. the installation time); `done_at` is stamped when it is completed.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    assigned_to_id: int  # ارجاع‌شونده
    scheduled_at: datetime | None = None  # زمان انجام (مثلاً زمان نصب)
    invoice_id: int | None = None


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    assigned_to_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    scheduled_at: datetime | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    created_by_id: int
    assigned_to_id: int
    status: TaskStatus
    scheduled_at: datetime | None
    done_at: datetime | None
    invoice_id: int | None
    created_at: datetime
