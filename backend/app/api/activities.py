"""Activity & project-stage routes — core bounded context.

Access model:
- Read  : any authenticated user.
- Write : manager or sales (activities); manager, sales or technical (stages).

Rules (blueprint):
- The activity is the central record tying customer + owner + type together.
- Project stages exist ONLY for activities of type `project`.
- This module drives work forward but never creates financial documents.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.activity import Activity, ProjectStage
from app.models.enums import ActivityType, UserRole
from app.models.party import Party
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityDetail,
    ActivityOut,
    ActivityUpdate,
    ProjectStageCreate,
    ProjectStageOut,
)

router = APIRouter(prefix="/api/activities", tags=["activities"])

can_write = require_roles(UserRole.manager, UserRole.sales)
can_stage = require_roles(UserRole.manager, UserRole.sales, UserRole.technical)


def _load_activity(activity_id: int, db: Session) -> Activity:
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "فعالیت یافت نشد")
    return activity


@router.get(
    "", response_model=list[ActivityOut], dependencies=[Depends(get_current_user)]
)
def list_activities(
    db: Session = Depends(get_db),
    customer_id: int | None = None,
    owner_id: int | None = None,
    type: ActivityType | None = None,
) -> list[Activity]:
    stmt = select(Activity).order_by(Activity.id.desc())
    if customer_id is not None:
        stmt = stmt.where(Activity.customer_id == customer_id)
    if owner_id is not None:
        stmt = stmt.where(Activity.owner_id == owner_id)
    if type is not None:
        stmt = stmt.where(Activity.type == type)
    return list(db.scalars(stmt))


@router.post(
    "",
    response_model=ActivityOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)) -> Activity:
    # Validate the cross-context references exist before linking.
    party = db.get(Party, payload.customer_id)
    if party is None or not party.is_customer:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "مشتری معتبر نیست")
    if db.get(User, payload.owner_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "کاربر مسئول معتبر نیست")

    activity = Activity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get(
    "/{activity_id}",
    response_model=ActivityDetail,
    dependencies=[Depends(get_current_user)],
)
def get_activity(activity_id: int, db: Session = Depends(get_db)) -> Activity:
    return _load_activity(activity_id, db)


@router.patch(
    "/{activity_id}",
    response_model=ActivityOut,
    dependencies=[Depends(can_write)],
)
def update_activity(
    activity_id: int, payload: ActivityUpdate, db: Session = Depends(get_db)
) -> Activity:
    activity = _load_activity(activity_id, db)
    data = payload.model_dump(exclude_unset=True)
    if "owner_id" in data and db.get(User, data["owner_id"]) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "کاربر مسئول معتبر نیست")
    for field, value in data.items():
        setattr(activity, field, value)
    db.commit()
    db.refresh(activity)
    return activity


# --- Project stages (sub-resource) ----------------------------------------

@router.get(
    "/{activity_id}/stages",
    response_model=list[ProjectStageOut],
    dependencies=[Depends(get_current_user)],
)
def list_stages(activity_id: int, db: Session = Depends(get_db)) -> list[ProjectStage]:
    _load_activity(activity_id, db)
    stmt = (
        select(ProjectStage)
        .where(ProjectStage.activity_id == activity_id)
        .order_by(ProjectStage.id)
    )
    return list(db.scalars(stmt))


@router.post(
    "/{activity_id}/stages",
    response_model=ProjectStageOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_stage)],
)
def add_stage(
    activity_id: int, payload: ProjectStageCreate, db: Session = Depends(get_db)
) -> ProjectStage:
    activity = _load_activity(activity_id, db)
    if activity.type != ActivityType.project:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "مراحل پروژه فقط برای فعالیت از نوع «پروژه» قابل ثبت است",
        )
    stage = ProjectStage(activity_id=activity_id, **payload.model_dump())
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage
