from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.enums import FinancialPeriodStatus


class FinancialPeriodBase(BaseModel):
    start_date: date
    end_date: date
    status: FinancialPeriodStatus = FinancialPeriodStatus.OPEN

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")

        return self


class FinancialPeriodCreate(FinancialPeriodBase):
    company_id: UUID


class FinancialPeriodUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: FinancialPeriodStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be greater than or equal to start_date")

        return self


class FinancialPeriodResponse(FinancialPeriodBase):
    id: UUID
    company_id: UUID

    model_config = ConfigDict(from_attributes=True)