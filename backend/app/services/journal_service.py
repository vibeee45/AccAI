from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.accounting.validators import validate_balanced_entry
from app.models.journal import JournalEntry, JournalLine
from app.models.enums import JournalStatus
from app.repositories.account_repository import AccountRepository
from app.repositories.journal_repository import JournalRepository
from app.repositories.transaction_repository import (
    TransactionRepository,
)
from app.schemas.journal import JournalEntryCreate


class JournalService:

    def __init__(self, db: Session):
        self.db = db

        self.repository = JournalRepository(db)
        self.account_repository = AccountRepository(db)
        self.transaction_repository = TransactionRepository(db)

    def get_entry(
        self,
        entry_id: UUID,
    ) -> JournalEntry:

        entry = self.repository.get_entry_by_id(
            entry_id
        )

        if entry is None:
            raise ValueError(
                "Journal entry not found"
            )

        return entry

    def list_entries(
        self,
        company_id: UUID,
    ) -> list[JournalEntry]:

        return self.repository.list_by_company(
            company_id
        )

    def create_entry(
        self,
        data: JournalEntryCreate,
    ) -> JournalEntry:

        # 1. Validate journal balance.
        validate_balanced_entry(data.lines)

        # 2. Validate transaction ownership.
        if data.transaction_id is not None:

            transaction = (
                self.transaction_repository.get_by_id(
                    data.transaction_id
                )
            )

            if transaction is None:
                raise ValueError(
                    "Transaction not found"
                )

            if transaction.company_id != data.company_id:
                raise ValueError(
                    "Transaction does not belong to the company"
                )

        # 3. Validate every account.
        for line in data.lines:

            account = self.account_repository.get_by_id(
                line.account_id
            )

            if account is None:
                raise ValueError(
                    f"Account {line.account_id} not found"
                )

            if account.company_id != data.company_id:
                raise ValueError(
                    "Journal account does not belong to the company"
                )

            if not account.is_active:
                raise ValueError(
                    f"Account '{account.name}' is inactive"
                )

        # 4. Generate entry number.
        entry_number = (
            self.repository.get_next_entry_number(
                data.company_id
            )
        )

        # 5. Create journal entry.
        entry = JournalEntry(
            company_id=data.company_id,
            transaction_id=data.transaction_id,
            entry_number=entry_number,
            entry_date=data.entry_date,
            description=data.description,
            status=data.status,
        )

        # 6. Create journal lines.
        lines = []

        for line_data in data.lines:

            line = JournalLine(
                account_id=line_data.account_id,
                debit=line_data.debit,
                credit=line_data.credit,
                line_description=line_data.line_description,
            )

            lines.append(line)

        self.repository.create_entry_with_lines(
            entry,
            lines,
        )

        self.db.commit()
        self.db.refresh(entry)

        return entry