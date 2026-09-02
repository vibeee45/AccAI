from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import JournalStatus


class JournalLineBase(BaseModel):
    account_id: UUID
    debit: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    line_description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_debit_credit(self):
        debit_positive = self.debit > Decimal("0")
        credit_positive = self.credit > Decimal("0")

        if debit_positive == credit_positive:
            raise ValueError(
                "A journal line must contain either a debit or a credit, not both."
            )

        return self


class JournalLineCreate(JournalLineBase):
    pass


class JournalLineResponse(JournalLineBase):
    id: UUID
    journal_entry_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalEntryBase(BaseModel):
    entry_date: date
    description: str = Field(min_length=1, max_length=2000)
    status: JournalStatus = JournalStatus.DRAFT


class JournalEntryCreate(JournalEntryBase):
    company_id: UUID
    transaction_id: UUID | None = None
    lines: list[JournalLineCreate] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_balanced_entry(self):
        total_debit = sum(
            (line.debit for line in self.lines),
            Decimal("0.00"),
        )

        total_credit = sum(
            (line.credit for line in self.lines),
            Decimal("0.00"),
        )

        if total_debit != total_credit:
            raise ValueError(
                f"Journal entry must be balanced. "
                f"Debit={total_debit}, Credit={total_credit}"
            )

        return self


class JournalEntryUpdate(BaseModel):
    entry_date: date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    status: JournalStatus | None = None


class JournalEntryResponse(JournalEntryBase):
    id: UUID
    company_id: UUID
    transaction_id: UUID 
    entry_number: int
    created_at: datetime
    lines: list[JournalLineResponse] = []

    model_config = ConfigDict(from_attributes=True)