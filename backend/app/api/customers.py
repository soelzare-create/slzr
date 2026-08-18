"""Customer routes — CRM bounded context.

Access model:
- Read  : any authenticated user.
- Write : manager or sales.

Rule (blueprint): the CRM only holds customer information; it has nothing to do
with invoices or inventory.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.customer import Customer
from app.models.enums import UserRole
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/api/customers", tags=["customers"])

can_write = require_roles(UserRole.manager, UserRole.sales)


@router.get(
    "", response_model=list[CustomerOut], dependencies=[Depends(get_current_user)]
)
def list_customers(
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="جستجو در نام"),
) -> list[Customer]:
    stmt = select(Customer).order_by(Customer.id.desc())
    if q:
        stmt = stmt.where(Customer.name.ilike(f"%{q}%"))
    return list(db.scalars(stmt))


@router.post(
    "",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_customer(
    payload: CustomerCreate, db: Session = Depends(get_db)
) -> Customer:
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get(
    "/{customer_id}",
    response_model=CustomerOut,
    dependencies=[Depends(get_current_user)],
)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مشتری یافت نشد")
    return customer


@router.patch(
    "/{customer_id}",
    response_model=CustomerOut,
    dependencies=[Depends(can_write)],
)
def update_customer(
    customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)
) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "مشتری یافت نشد")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer
