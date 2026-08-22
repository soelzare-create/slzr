"""Task routes — internal referrals (ارجاعات).

Replaces the old ticketing. Any authenticated employee can refer a task to
another (including to their manager). A user sees tasks assigned to them and
tasks they created; managers see everything. The assignee (or the creator, or a
manager) can advance the status; moving to «done» stamps the completion time.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.enums import TaskStatus, UserRole
from app.models.support import Task
from app.models.user import User
from app.schemas.support import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _may_touch(task: Task, user: User) -> bool:
    return (
        user.role == UserRole.manager
        or task.assigned_to_id == user.id
        or task.created_by_id == user.id
    )


@router.get("", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    assigned_to_id: int | None = None,
    created_by_id: int | None = None,
    status_: TaskStatus | None = Query(default=None, alias="status"),
    scope: str | None = Query(default=None),  # "assigned" | "created" | None
) -> list[Task]:
    stmt = select(Task).order_by(Task.id.desc())
    # Managers see all; everyone else sees tasks they created or were assigned.
    if user.role != UserRole.manager:
        stmt = stmt.where(
            or_(Task.assigned_to_id == user.id, Task.created_by_id == user.id)
        )
    if scope == "assigned":
        stmt = stmt.where(Task.assigned_to_id == user.id)
    elif scope == "created":
        stmt = stmt.where(Task.created_by_id == user.id)
    if assigned_to_id is not None:
        stmt = stmt.where(Task.assigned_to_id == assigned_to_id)
    if created_by_id is not None:
        stmt = stmt.where(Task.created_by_id == created_by_id)
    if status_ is not None:
        stmt = stmt.where(Task.status == status_)
    return list(db.scalars(stmt))


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    assignee = db.get(User, payload.assigned_to_id)
    if assignee is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "کاربر ارجاع‌شونده معتبر نیست")
    task = Task(
        title=payload.title,
        description=payload.description,
        created_by_id=user.id,
        assigned_to_id=payload.assigned_to_id,
        scheduled_at=payload.scheduled_at,
        invoice_id=payload.invoice_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "کار یافت نشد")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "کار یافت نشد")
    if not _may_touch(task, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "اجازهٔ تغییر این کار را ندارید")

    data = payload.model_dump(exclude_unset=True)
    if "assigned_to_id" in data and db.get(User, data["assigned_to_id"]) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "کاربر ارجاع‌شونده معتبر نیست")

    for field, value in data.items():
        setattr(task, field, value)

    # stamp/clear the completion time as the status crosses «done»
    if "status" in data:
        if data["status"] == TaskStatus.done and task.done_at is None:
            task.done_at = datetime.now(timezone.utc)
        elif data["status"] != TaskStatus.done:
            task.done_at = None

    db.commit()
    db.refresh(task)
    return task
