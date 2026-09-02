from uuid import UUID

from sqlalchemy.orm import Session
from app.models.enums import (
    FinancialPeriodStatus,
    TransactionStatus,
)
from app.models.enums import TransactionStatus
from app.models.transaction import Transaction
from app.repositories.transaction_repository import (
    TransactionRepository,
)
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
)
from app.services.company_service import CompanyService
from app.services.financial_period_service import (
    FinancialPeriodService,
)


class TransactionService:

    def __init__(self, db: Session):
        self.db = db

        self.repository = TransactionRepository(db)
        self.company_service = CompanyService(db)
        self.period_service = FinancialPeriodService(db)

    def get_transaction(
        self,
        transaction_id: UUID,
    ) -> Transaction:

        transaction = self.repository.get_by_id(
            transaction_id
        )

        if transaction is None:
            raise ValueError(
                "Transaction not found"
            )

        return transaction

    def list_transactions(
        self,
        company_id: UUID,
        status: TransactionStatus | None = None,
    ) -> list[Transaction]:

        self.company_service.get_company(company_id)

        return self.repository.list_by_company(
            company_id,
            status=status,
        )

    def create_transaction(
        self,
        data: TransactionCreate,
    ) -> Transaction:

        self.company_service.get_company(
            data.company_id
        )

        period = self.period_service.get_period(
            data.financial_period_id
        )

        if period.company_id != data.company_id:
            raise ValueError(
                "Financial period does not belong to the company"
            )

        if not (
            period.start_date
            <= data.transaction_date
            <= period.end_date
        ):
            raise ValueError(
                "Transaction date falls outside the financial period"
            )

        if period.status != FinancialPeriodStatus.OPEN:
            raise ValueError(
                "Transactions can only be created in an OPEN financial period"
            )

        transaction = Transaction(
            company_id=data.company_id,
            financial_period_id=data.financial_period_id,
            transaction_date=data.transaction_date,
            description=data.description,
            amount=data.amount,
            source_file_id=data.source_file_id,
            source_row_number=data.source_row_number,
            status=TransactionStatus.PENDING,
        )

        self.repository.create(transaction)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def update_transaction(
        self,
        transaction_id: UUID,
        data: TransactionUpdate,
    ) -> Transaction:

        transaction = self.get_transaction(
            transaction_id
        )

        if transaction.status == TransactionStatus.POSTED:
            raise ValueError(
                "Posted transactions cannot be modified"
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "transaction_date" in update_data:

            period = self.period_service.get_period(
                transaction.financial_period_id
            )

            new_date = update_data["transaction_date"]

            if not (
                period.start_date
                <= new_date
                <= period.end_date
            ):
                raise ValueError(
                    "Transaction date falls outside the financial period"
                )

        for field, value in update_data.items():
            setattr(transaction, field, value)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction