"""Party model — the single record for anyone the company deals with.

A party can act as a customer (we sell to them), a supplier (we buy from them),
or BOTH — without ever being duplicated. This keeps a single source of truth,
in line with the brand philosophy «همه چیز سر جای خودش», and lets accounting
compute one net balance per party.

Formerly the CRM-only `customers` table; generalized so the purchase side of the
business is a first-class citizen alongside sales.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ContactPosition
from app.models.mixins import TimestampMixin


class Party(Base, TimestampMixin):
    """طرف‌حساب — مشتری و/یا تأمین‌کننده."""

    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # نام شخص/سازمان
    phone: Mapped[str | None] = mapped_column(String(30), index=True)  # شماره تماس
    address: Mapped[str | None] = mapped_column(String(500))  # نشانی

    # Roles — a party may be either, both, or (briefly) neither.
    is_customer: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # مشتری هست
    is_supplier: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # تأمین‌کننده هست

    # CRM fields (meaningful mainly for the customer role).
    contact_date: Mapped[date | None] = mapped_column(Date)  # تاریخ آشنایی
    referral_source: Mapped[str | None] = mapped_column(String(200))  # مدل آشنایی

    # Contact people inside this party's organization (افراد رابط).
    contacts: Mapped[list["PartyContact"]] = relationship(
        "PartyContact",
        back_populates="party",
        cascade="all, delete-orphan",
        order_by="PartyContact.id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        roles = []
        if self.is_customer:
            roles.append("customer")
        if self.is_supplier:
            roles.append("supplier")
        return f"<Party {self.id} {self.name} [{'+'.join(roles) or 'none'}]>"


class PartyContact(Base, TimestampMixin):
    """فردِ رابط درون سازمانِ یک طرف‌حساب — با سمت مشخص.

    به ما اجازه می‌دهد در آینده به هر بخش سازمان (خرید، مالی، فنی، …) وصل شویم.
    هر رکورد نگه می‌دارد که «کدام کاربرِ ما» آن را ثبت کرده است.
    """

    __tablename__ = "party_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    party_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # نام فرد
    phone: Mapped[str | None] = mapped_column(String(30))  # شماره تماس
    position: Mapped[ContactPosition] = mapped_column(
        Enum(ContactPosition, native_enum=False, length=20), nullable=False
    )  # سمت (اجباری)
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )  # چه کسی این فرد را ثبت کرده

    party: Mapped["Party"] = relationship("Party", back_populates="contacts")
    created_by: Mapped["User"] = relationship("User")  # noqa: F821

    @property
    def created_by_name(self) -> str | None:  # exposed on the API for display
        return self.created_by.name if self.created_by else None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PartyContact {self.id} {self.name} ({self.position.value})>"
