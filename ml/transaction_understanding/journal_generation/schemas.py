from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


ZERO = Decimal("0")


@dataclass(frozen=True)
class JournalLine:
    account_id: str
    account_name: str
    description: str
    debit: Decimal
    credit: Decimal

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name.strip():
            raise ValueError(
                "account_name cannot be empty."
            )

        if not self.description.strip():
            raise ValueError(
                "description cannot be empty."
            )

        if not isinstance(self.debit, Decimal):
            raise TypeError(
                "debit must be Decimal."
            )

        if not isinstance(self.credit, Decimal):
            raise TypeError(
                "credit must be Decimal."
            )

        if self.debit < ZERO:
            raise ValueError(
                "debit cannot be negative."
            )

        if self.credit < ZERO:
            raise ValueError(
                "credit cannot be negative."
            )

        if self.debit > ZERO and self.credit > ZERO:
            raise ValueError(
                "A journal line cannot contain "
                "both debit and credit."
            )

        if self.debit == ZERO and self.credit == ZERO:
            raise ValueError(
                "A journal line must contain "
                "either debit or credit."
            )


@dataclass(frozen=True)
class JournalEntry:
    journal_id: str
    transaction_id: str
    narration: str
    amount: Decimal
    lines: tuple[JournalLine, ...]

    transaction_class: str
    payment_mode: str

    ai_confidence: float
    requires_review: bool

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.journal_id.strip():
            raise ValueError(
                "journal_id cannot be empty."
            )

        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not self.narration.strip():
            raise ValueError(
                "narration cannot be empty."
            )

        if not isinstance(self.amount, Decimal):
            raise TypeError(
                "amount must be Decimal."
            )

        if self.amount <= ZERO:
            raise ValueError(
                "amount must be greater than zero."
            )

        if not isinstance(self.lines, tuple):
            raise TypeError(
                "lines must be a tuple."
            )

        if len(self.lines) < 2:
            raise ValueError(
                "A journal entry requires at least "
                "two journal lines."
            )

        if not 0.0 <= self.ai_confidence <= 1.0:
            raise ValueError(
                "ai_confidence must be between 0 and 1."
            )

        if not self.transaction_class.strip():
            raise ValueError(
                "transaction_class cannot be empty."
            )

        if not self.payment_mode.strip():
            raise ValueError(
                "payment_mode cannot be empty."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

        total_debit = sum(
            (line.debit for line in self.lines),
            ZERO,
        )

        total_credit = sum(
            (line.credit for line in self.lines),
            ZERO,
        )

        if total_debit != total_credit:
            raise ValueError(
                "Journal entry is not balanced."
            )

        if total_debit != self.amount:
            raise ValueError(
                "Journal total must equal "
                "transaction amount."
            )


@dataclass(frozen=True)
class JournalGenerationResult:
    success: bool
    journal: JournalEntry | None

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.success and self.journal is None:
            raise ValueError(
                "Successful result must contain a journal."
            )

        if not self.success and self.journal is not None:
            raise ValueError(
                "Failed result cannot contain a journal."
            )

        if not isinstance(self.errors, tuple):
            raise TypeError(
                "errors must be a tuple."
            )

        if not isinstance(self.warnings, tuple):
            raise TypeError(
                "warnings must be a tuple."
            )
