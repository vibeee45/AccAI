from __future__ import annotations

from decimal import Decimal
from typing import Iterable


class AccountingValidationError(ValueError):
    """Raised when an accounting rule is violated."""


def validate_positive_amount(amount: Decimal) -> None:
    """Ensure an accounting amount is strictly positive."""

    if amount <= Decimal("0"):
        raise AccountingValidationError(
            "Accounting amount must be greater than zero."
        )


def validate_debit_credit(
    debit: Decimal,
    credit: Decimal,
) -> None:
    """
    Validate one double-entry journal line.

    Exactly one side must contain a positive amount.
    """

    if debit < Decimal("0"):
        raise AccountingValidationError(
            "Debit amount cannot be negative."
        )

    if credit < Decimal("0"):
        raise AccountingValidationError(
            "Credit amount cannot be negative."
        )

    debit_positive = debit > Decimal("0")
    credit_positive = credit > Decimal("0")

    if debit_positive and credit_positive:
        raise AccountingValidationError(
            "A journal line cannot contain both debit and credit."
        )

    if not debit_positive and not credit_positive:
        raise AccountingValidationError(
            "A journal line must contain either debit or credit."
        )


def validate_balanced_entry(
    lines: Iterable[tuple[Decimal, Decimal]],
) -> None:
    """
    Validate that total debits equal total credits.

    Each item must be:
        (debit, credit)
    """

    lines = list(lines)

    if len(lines) < 2:
        raise AccountingValidationError(
            "A journal entry must contain at least two lines."
        )

    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for debit, credit in lines:
        validate_debit_credit(debit, credit)

        total_debit += debit
        total_credit += credit

    if total_debit != total_credit:
        raise AccountingValidationError(
            "Journal entry is not balanced: "
            f"Debit={total_debit}, Credit={total_credit}."
        )


def validate_journal_lines(lines) -> None:
    """
    Validate journal-line objects.

    Expected attributes:
        debit
        credit
    """

    validate_balanced_entry(
        (line.debit, line.credit)
        for line in lines
    )