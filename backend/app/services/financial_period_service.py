from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import FinancialPeriodStatus
from app.models.financial_period import FinancialPeriod
from app.repositories.company_repository import CompanyRepository
from app.repositories.financial_period_repository import (
    FinancialPeriodRepository,
)
from app.schemas.financial_period import (
    FinancialPeriodCreate,
    FinancialPeriodUpdate,
)


class FinancialPeriodService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = FinancialPeriodRepository(db)
        self.company_repository = CompanyRepository(db)

    def get_period(
        self,
        period_id: UUID,
    ) -> FinancialPeriod:

        period = self.repository.get_by_id(period_id)

        if period is None:
            raise ValueError(
                "Financial period not found"
            )

        return period

    def list_periods(
        self,
        company_id: UUID,
    ) -> list[FinancialPeriod]:

        company = self.company_repository.get_by_id(
            company_id
        )

        if company is None:
            raise ValueError("Company not found")

        return self.repository.list_by_company(
            company_id
        )

    def create_period(
        self,
        data: FinancialPeriodCreate,
    ) -> FinancialPeriod:

        company = self.company_repository.get_by_id(
            data.company_id
        )

        if company is None:
            raise ValueError("Company not found")

        existing_periods = self.repository.list_by_company(
            data.company_id
        )

        for existing in existing_periods:

            overlaps = (
                data.start_date <= existing.end_date
                and data.end_date >= existing.start_date
            )

            if overlaps:
                raise ValueError(
                    "Financial period overlaps an existing period"
                )

        period = FinancialPeriod(
            company_id=data.company_id,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status,
        )

        self.repository.create(period)

        self.db.commit()
        self.db.refresh(period)

        return period

    def update_period(
        self,
        period_id: UUID,
        data: FinancialPeriodUpdate,
    ) -> FinancialPeriod:

        period = self.get_period(period_id)

        if period.status == FinancialPeriodStatus.LOCKED:
            raise ValueError(
                "Locked financial periods cannot be modified"
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        start_date = update_data.get(
            "start_date",
            period.start_date,
        )

        end_date = update_data.get(
            "end_date",
            period.end_date,
        )

        if end_date < start_date:
            raise ValueError(
                "end_date must be greater than or equal to start_date"
            )

        existing_periods = self.repository.list_by_company(
            period.company_id
        )

        for existing in existing_periods:

            if existing.id == period.id:
                continue

            overlaps = (
                start_date <= existing.end_date
                and end_date >= existing.start_date
            )

            if overlaps:
                raise ValueError(
                    "Financial period overlaps an existing period"
                )

        for field, value in update_data.items():
            setattr(period, field, value)

        self.db.commit()
        self.db.refresh(period)

        return period

    def get_open_period_for_date(
        self,
        company_id: UUID,
        transaction_date: date,
    ) -> FinancialPeriod:

        period = self.repository.get_open_period(
            company_id,
            transaction_date,
        )

        if period is None:
            raise ValueError(
                "No open financial period exists for this date"
            )

        return period