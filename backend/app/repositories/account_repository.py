from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import ChartOfAccount


class AccountRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        account_id: UUID,
    ) -> ChartOfAccount | None:

        return self.db.get(
            ChartOfAccount,
            account_id,
        )

    def get_by_company_and_code(
        self,
        company_id: UUID,
        code: str,
    ) -> ChartOfAccount | None:

        statement = select(ChartOfAccount).where(
            ChartOfAccount.company_id == company_id,
            ChartOfAccount.code == code,
        )

        return self.db.scalar(statement)

    def list_by_company(
        self,
        company_id: UUID,
        active_only: bool = False,
    ) -> list[ChartOfAccount]:

        statement = select(ChartOfAccount).where(
            ChartOfAccount.company_id == company_id
        )

        if active_only:
            statement = statement.where(
                ChartOfAccount.is_active.is_(True)
            )

        statement = statement.order_by(
            ChartOfAccount.code
        )

        return list(self.db.scalars(statement).all())

    def create(
        self,
        account: ChartOfAccount,
    ) -> ChartOfAccount:

        self.db.add(account)
        self.db.flush()

        return account

    def delete(
        self,
        account: ChartOfAccount,
    ) -> None:

        self.db.delete(account)

    def get_parent(
        self,
        parent_id: UUID,
    ) -> ChartOfAccount | None:

        return self.db.get(
            ChartOfAccount,
            parent_id,
        )