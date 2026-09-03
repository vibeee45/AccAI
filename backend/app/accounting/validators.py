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


def _extract_debit_credit(line) -> tuple[Decimal, Decimal]:
    """
    Extract debit and credit amounts from either:

    1. A tuple/list:
       (debit, credit)

    2. An object containing:
       line.debit
       line.credit

    This keeps the accounting engine compatible with
    both pure accounting objects and Pydantic schemas.
    """

    if hasattr(line, "debit") and hasattr(line, "credit"):
        return (
            Decimal(str(line.debit)),
            Decimal(str(line.credit)),
        )

    if isinstance(line, (tuple, list)) and len(line) == 2:
        return (
            Decimal(str(line[0])),
            Decimal(str(line[1])),
        )

    raise AccountingValidationError(
        "Invalid journal line. Expected "
        "(debit, credit) or an object with debit and credit."
    )


def validate_balanced_entry(
    lines: Iterable,
) -> None:
    """
    Validate that total debits equal total credits.

    Supports both:

        (debit, credit)

    and objects with:

        .debit
        .credit
    """

    lines = list(lines)

    if len(lines) < 2:
        raise AccountingValidationError(
            "A journal entry must contain at least two lines."
        )

    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    for line in lines:
        debit, credit = _extract_debit_credit(line)

        validate_debit_credit(
            debit,
            credit,
        )

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
    """

    validate_balanced_entry(lines)