from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.accounting.normalization import NormalizedTransaction
from app.accounting.validators import (
    AccountingValidationError,
    validate_balanced_entry,
)


@dataclass(frozen=True)
class JournalLineData:
    """Pure accounting representation of a journal line."""

    account: str
    debit: Decimal
    credit: Decimal
    description: str


@dataclass(frozen=True)
class JournalEntryData:
    """Pure accounting representation of a journal entry."""

    transaction_id: UUID | None
    entry_date: object
    description: str
    lines: tuple[JournalLineData, ...]

    @property
    def total_debit(self) -> Decimal:
        return sum(
            (line.debit for line in self.lines),
            Decimal("0"),
        )

    @property
    def total_credit(self) -> Decimal:
        return sum(
            (line.credit for line in self.lines),
            Decimal("0"),
        )

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit


def generate_two_line_journal(
    transaction: NormalizedTransaction,
) -> JournalEntryData:
    """
    Generate a basic two-sided journal entry.

    Example:

        Purchases Dr    50,000
            To Cash              50,000
    """

    if not transaction.debit_account:
        raise AccountingValidationError(
            "Debit account is required to generate a journal."
        )

    if not transaction.credit_account:
        raise AccountingValidationError(
            "Credit account is required to generate a journal."
        )

    if transaction.amount <= Decimal("0"):
        raise AccountingValidationError(
            "Journal amount must be greater than zero."
        )

    if (
        transaction.debit_account.strip().lower()
        == transaction.credit_account.strip().lower()
    ):
        raise AccountingValidationError(
            "Debit and credit accounts cannot be the same."
        )

    lines = (
        JournalLineData(
            account=transaction.debit_account,
            debit=transaction.amount,
            credit=Decimal("0.00"),
            description=transaction.description,
        ),
        JournalLineData(
            account=transaction.credit_account,
            debit=Decimal("0.00"),
            credit=transaction.amount,
            description=transaction.description,
        ),
    )

    validate_balanced_entry(
        (line.debit, line.credit)
        for line in lines
    )

    return JournalEntryData(
        transaction_id=transaction.transaction_id,
        entry_date=transaction.transaction_date,
        description=transaction.description,
        lines=lines,
    )


def validate_journal_entry(
    journal_entry: JournalEntryData,
) -> JournalEntryData:
    """Validate an already generated journal entry."""

    if not journal_entry.description.strip():
        raise AccountingValidationError(
            "Journal description cannot be empty."
        )

    if len(journal_entry.lines) < 2:
        raise AccountingValidationError(
            "Journal entry must contain at least two lines."
        )

    validate_balanced_entry(
        (line.debit, line.credit)
        for line in journal_entry.lines
    )

    return journal_entry


def generate_journal(
    transaction: NormalizedTransaction,
) -> JournalEntryData:
    """
    Main journal-generation entry point.

    Currently supports a standard two-account transaction.
    More complex transaction types can be added later without
    changing the accounting pipeline.
    """

    journal = generate_two_line_journal(transaction)

    return validate_journal_entry(journal)