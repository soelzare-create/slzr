"""Support routes — ticketing (فاز ۶).

A ticket ties a customer issue to, optionally, the specific device it concerns
(a serialized stock unit). Support drives the issue to resolution; it does not
touch inventory or accounting.

Access model:
- Read  : any authenticated user.
- Write : manager, technical, or sales (customer-facing roles).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import TicketStatus, UserRole
from app.models.inventory import StockItem
from app.models.party import Party
from app.models.support import Ticket
from app.models.user import User
from app.schemas.support import TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/api/tickets", tags=["support"])

can_write = require_roles(UserRole.manager, UserRole.technical, UserRole.sales)


def _validate_device(db: Session, device_unit_id: int | None) -> None:
    """A ticket's device, if given, must be a serialized stock unit."""
    if device_unit_id is None:
        return
    unit = db.get(StockItem, device_unit_id)
    if unit is None or unit.serial_number is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "دستگاه (تک‌کالای سریال‌دار) معتبر نیست"
        )


def _validate_owner(db: Session, owner_id: int | None) -> None:
    if owner_id is not None and db.get(User, owner_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "کاربر مسئول معتبر نیست")


@router.get("", response_model=list[TicketOut], dependencies=[Depends(get_current_user)])
def list_tickets(
    db: Session = Depends(get_db),
    customer_id: int | None = None,
    owner_id: int | None = None,
    status_: TicketStatus | None = Query(default=None, alias="status"),
) -> list[Ticket]:
    stmt = select(Ticket).order_by(Ticket.id.desc())
    if customer_id is not None:
        stmt = stmt.where(Ticket.customer_id == customer_id)
    if owner_id is not None:
        stmt = stmt.where(Ticket.owner_id == owner_id)
    if status_ is not None:
        stmt = stmt.where(Ticket.status == status_)
    return list(db.scalars(stmt))


@router.post(
    "", response_model=TicketOut, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_write)],
)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> Ticket:
    customer = db.get(Party, payload.customer_id)
    if customer is None or not customer.is_customer:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "مشتری معتبر نیست")
    _validate_device(db, payload.device_unit_id)
    _validate_owner(db, payload.owner_id)

    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get(
    "/{ticket_id}", response_model=TicketOut, dependencies=[Depends(get_current_user)]
)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "تیکت یافت نشد")
    return ticket


@router.patch(
    "/{ticket_id}", response_model=TicketOut, dependencies=[Depends(can_write)]
)
def update_ticket(
    ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "تیکت یافت نشد")
    data = payload.model_dump(exclude_unset=True)
    if "owner_id" in data:
        _validate_owner(db, data["owner_id"])
    for field, value in data.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket
