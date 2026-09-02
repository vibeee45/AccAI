from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType, NormalBalance


class AccountBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    account_type: AccountType
    normal_balance: NormalBalance
    is_active: bool = True
    parent_id: UUID | None = None


class AccountCreate(AccountBase):
    company_id: UUID


class AccountUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    account_type: AccountType | None = None
    normal_balance: NormalBalance | None = None
    is_active: bool | None = None
    parent_id: UUID | None = None


class AccountResponse(AccountBase):
    id: UUID
    company_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)