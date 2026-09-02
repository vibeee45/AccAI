from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.enums import TransactionStatus


class TransactionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        transaction_id: UUID,
    ) -> Transaction | None:

        return self.db.get(
            Transaction,
            transaction_id,
        )

    def list_by_company(
        self,
        company_id: UUID,
        status: TransactionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Transaction]:

        statement = select(Transaction).where(
            Transaction.company_id == company_id
        )

        if status is not None:
            statement = statement.where(
                Transaction.status == status
            )

        if start_date is not None:
            statement = statement.where(
                Transaction.transaction_date >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                Transaction.transaction_date <= end_date
            )

        statement = statement.order_by(
            Transaction.transaction_date,
            Transaction.created_at,
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        transaction: Transaction,
    ) -> Transaction:

        self.db.add(transaction)
        self.db.flush()

        return transaction

    def update(
        self,
        transaction: Transaction,
    ) -> Transaction:

        self.db.add(transaction)
        self.db.flush()

        return transaction

    def delete(
        self,
        transaction: Transaction,
    ) -> None:

        self.db.delete(transaction)