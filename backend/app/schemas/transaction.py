from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransactionStatus


class TransactionBase(BaseModel):
    transaction_date: date
    description: str = Field(min_length=1, max_length=2000)
    amount: Decimal = Field(ge=0, decimal_places=2)


class TransactionCreate(TransactionBase):
    company_id: UUID
    financial_period_id: UUID
    source_file_id: UUID | None = None
    source_row_number: int | None = Field(default=None, ge=1)


class TransactionUpdate(BaseModel):
    transaction_date: date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    status: TransactionStatus | None = None


class TransactionResponse(TransactionBase):
    id: UUID
    company_id: UUID
    financial_period_id: UUID
    source_file_id: UUID | None
    source_row_number: int | None
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)