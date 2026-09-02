from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CompanyRole


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    financial_year_start: date


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    financial_year_start: date | None = None


class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyUserCreate(BaseModel):
    user_id: UUID
    role: CompanyRole = CompanyRole.VIEWER


class CompanyUserUpdate(BaseModel):
    role: CompanyRole


class CompanyUserResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    role: CompanyRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)