"""User schemas (input/output DTOs for the presentation layer)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: UserRole
    phone: str = Field(min_length=3, max_length=30)
    address: str | None = None
    emergency_contact: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    role: UserRole | None = None
    address: str | None = None
    emergency_contact: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
