from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_period import FinancialPeriod
from app.models.enums import FinancialPeriodStatus


class FinancialPeriodRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        period_id: UUID,
    ) -> FinancialPeriod | None:

        return self.db.get(
            FinancialPeriod,
            period_id,
        )

    def list_by_company(
        self,
        company_id: UUID,
    ) -> list[FinancialPeriod]:

        statement = (
            select(FinancialPeriod)
            .where(
                FinancialPeriod.company_id == company_id
            )
            .order_by(
                FinancialPeriod.start_date
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_open_period(
        self,
        company_id: UUID,
        transaction_date: date,
    ) -> FinancialPeriod | None:

        statement = select(FinancialPeriod).where(
            FinancialPeriod.company_id == company_id,
            FinancialPeriod.start_date <= transaction_date,
            FinancialPeriod.end_date >= transaction_date,
            FinancialPeriod.status == FinancialPeriodStatus.OPEN,
        )

        return self.db.scalar(statement)

    def create(
        self,
        period: FinancialPeriod,
    ) -> FinancialPeriod:

        self.db.add(period)
        self.db.flush()

        return period