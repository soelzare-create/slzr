"""Team directory — minimal, read-only user list for assignment dropdowns.

Any authenticated user may read this (unlike /api/users, which is manager-only
for administration). It exposes only id/name/role — no contact or auth data.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/api/team", tags=["team"])


class TeamMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: UserRole


@router.get("", response_model=list[TeamMember], dependencies=[Depends(get_current_user)])
def list_team(db: Session = Depends(get_db)) -> list[User]:
    stmt = select(User).where(User.is_active.is_(True)).order_by(User.name)
    return list(db.scalars(stmt))
