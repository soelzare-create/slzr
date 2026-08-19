"""Party schemas — customer and/or supplier."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ContactPosition


class PartyContactBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)  # نام فرد
    phone: str | None = Field(default=None, max_length=30)
    position: ContactPosition  # سمت — اجباری، از فهرست انتخابی


class PartyContactCreate(PartyContactBase):
    pass


class PartyContactOut(PartyContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    party_id: int
    created_by_id: int
    created_by_name: str | None = None
    created_at: datetime


class PartyBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    is_customer: bool = True
    is_supplier: bool = False
    contact_date: date | None = None
    referral_source: str | None = Field(default=None, max_length=200)


class PartyCreate(PartyBase):
    @model_validator(mode="after")
    def at_least_one_role(self) -> "PartyCreate":
        if not (self.is_customer or self.is_supplier):
            raise ValueError("طرف‌حساب باید حداقل یک نقش داشته باشد (مشتری یا تأمین‌کننده)")
        return self


class PartyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    is_customer: bool | None = None
    is_supplier: bool | None = None
    contact_date: date | None = None
    referral_source: str | None = Field(default=None, max_length=200)


class PartyOut(PartyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    contacts: list[PartyContactOut] = []
