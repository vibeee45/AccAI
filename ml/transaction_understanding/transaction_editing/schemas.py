from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


EDITABLE_FIELDS = (
    "raw_text",
    "normalized_text",
    "amount",
    "transaction_class",
    "debit_account_id",
    "debit_account_name",
    "credit_account_id",
    "credit_account_name",
    "payment_mode",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EditableTransaction:
    """
    Snapshot of the transaction values that a human reviewer can edit.

    This is deliberately separate from TransactionPrediction so that
    human edits never mutate the original AI prediction.
    """

    transaction_id: str
    raw_text: str
    normalized_text: str
    amount: float
    transaction_class: str
    debit_account_id: str
    debit_account_name: str
    credit_account_id: str
    credit_account_name: str
    payment_mode: str

    def __post_init__(self) -> None:
        if not isinstance(self.transaction_id, str):
            raise TypeError("transaction_id must be a string.")

        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        string_fields = (
            self.raw_text,
            self.normalized_text,
            self.transaction_class,
            self.debit_account_id,
            self.debit_account_name,
            self.credit_account_id,
            self.credit_account_name,
            self.payment_mode,
        )

        if any(
            not isinstance(value, str)
            for value in string_fields
        ):
            raise TypeError(
                "Transaction text and account fields must be strings."
            )

        if any(
            not value.strip()
            for value in string_fields
        ):
            raise ValueError(
                "Transaction text and account fields cannot be empty."
            )

        if not isinstance(self.amount, (int, float, Decimal)):
            raise TypeError(
                "amount must be numeric."
            )

        if float(self.amount) <= 0:
            raise ValueError(
                "amount must be greater than 0."
            )

        if (
            self.debit_account_id.strip()
            == self.credit_account_id.strip()
        ):
            raise ValueError(
                "debit and credit account IDs must be distinct."
            )


@dataclass(frozen=True)
class TransactionEdit:
    """
    Represents a single human edit operation.

    old_value/new_value are intentionally stored as Any because
    amount is numeric while the remaining editable fields are strings.
    """

    field: str
    old_value: Any
    new_value: Any

    def __post_init__(self) -> None:
        if not isinstance(self.field, str):
            raise TypeError("field must be a string.")

        if self.field not in EDITABLE_FIELDS:
            raise ValueError(
                f"Unsupported editable field: {self.field}"
            )

        if self.old_value == self.new_value:
            raise ValueError(
                "old_value and new_value must be different."
            )


@dataclass(frozen=True)
class TransactionEditResult:
    """
    Immutable result containing the original transaction, edited
    transaction and complete list of changes.
    """

    original: EditableTransaction
    edited: EditableTransaction
    edits: tuple[TransactionEdit, ...]
    edited_at: datetime
    edited_by: str | None
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(
            self.original,
            EditableTransaction,
        ):
            raise TypeError(
                "original must be EditableTransaction."
            )

        if not isinstance(
            self.edited,
            EditableTransaction,
        ):
            raise TypeError(
                "edited must be EditableTransaction."
            )

        if (
            self.original.transaction_id
            != self.edited.transaction_id
        ):
            raise ValueError(
                "Original and edited transactions must have "
                "the same transaction_id."
            )

        if not isinstance(self.edits, tuple):
            raise TypeError(
                "edits must be a tuple."
            )

        if any(
            not isinstance(edit, TransactionEdit)
            for edit in self.edits
        ):
            raise TypeError(
                "All edits must be TransactionEdit."
            )

        if not isinstance(
            self.edited_at,
            datetime,
        ):
            raise TypeError(
                "edited_at must be datetime."
            )

        if self.edited_at.tzinfo is None:
            raise ValueError(
                "edited_at must be timezone-aware."
            )

        if self.edited_by is not None:
            if not isinstance(self.edited_by, str):
                raise TypeError(
                    "edited_by must be a string or None."
                )

            if not self.edited_by.strip():
                raise ValueError(
                    "edited_by cannot be empty."
                )

        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must be a string."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

    @property
    def changed_fields(self) -> tuple[str, ...]:
        return tuple(
            edit.field
            for edit in self.edits
        )

    @property
    def has_changes(self) -> bool:
        return bool(self.edits)
