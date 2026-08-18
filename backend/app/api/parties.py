"""Party routes — customers and/or suppliers over a single table.

Access model:
- Read  : any authenticated user.
- Write : manager, sales (customers), or warehouse (suppliers).

The `role` filter drives the customer view vs the supplier view in the UI, but
there is only ever one record per party (no duplication).
"""
from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.party import Party
from app.schemas.party import PartyCreate, PartyOut, PartyUpdate

router = APIRouter(prefix="/api/parties", tags=["parties"])

can_write = require_roles(UserRole.manager, UserRole.sales, UserRole.warehouse)


class RoleFilter(str, Enum):
    customer = "customer"
    supplier = "supplier"
    all = "all"


@router.get(
    "", response_model=list[PartyOut], dependencies=[Depends(get_current_user)]
)
def list_parties(
    db: Session = Depends(get_db),
    role: RoleFilter = Query(default=RoleFilter.all, description="فیلتر نقش"),
    q: str | None = Query(default=None, description="جستجو در نام"),
) -> list[Party]:
    stmt = select(Party).order_by(Party.id.desc())
    if role == RoleFilter.customer:
        stmt = stmt.where(Party.is_customer.is_(True))
    elif role == RoleFilter.supplier:
        stmt = stmt.where(Party.is_supplier.is_(True))
    if q:
        stmt = stmt.where(Party.name.ilike(f"%{q}%"))
    return list(db.scalars(stmt))


@router.post(
    "",
    response_model=PartyOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_party(payload: PartyCreate, db: Session = Depends(get_db)) -> Party:
    party = Party(**payload.model_dump())
    db.add(party)
    db.commit()
    db.refresh(party)
    return party


@router.get(
    "/{party_id}", response_model=PartyOut, dependencies=[Depends(get_current_user)]
)
def get_party(party_id: int, db: Session = Depends(get_db)) -> Party:
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "طرف‌حساب یافت نشد")
    return party


@router.patch(
    "/{party_id}", response_model=PartyOut, dependencies=[Depends(can_write)]
)
def update_party(
    party_id: int, payload: PartyUpdate, db: Session = Depends(get_db)
) -> Party:
    party = db.get(Party, party_id)
    if party is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "طرف‌حساب یافت نشد")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(party, field, value)

    # Never leave a party with no role.
    if not (party.is_customer or party.is_supplier):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "طرف‌حساب باید حداقل یک نقش داشته باشد",
        )
    db.commit()
    db.refresh(party)
    return party
