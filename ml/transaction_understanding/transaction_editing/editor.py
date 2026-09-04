from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

from ..prediction.schemas import TransactionPrediction
from .config import TransactionEditingConfig
from .schemas import (
    EditableTransaction,
    TransactionEdit,
    TransactionEditResult,
    utc_now,
)


class TransactionEditor:
    """
    Applies human edits to an AI prediction.

    The original prediction is never modified.
    """

    def __init__(
        self,
        config: TransactionEditingConfig | None = None,
    ) -> None:
        self.config = config or TransactionEditingConfig()

    def snapshot(
        self,
        prediction: TransactionPrediction,
    ) -> EditableTransaction:
        if not isinstance(
            prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        if prediction.amount is None:
            raise ValueError(
                "Cannot edit a prediction without an amount."
            )

        return EditableTransaction(
            transaction_id=prediction.transaction_id,
            raw_text=prediction.raw_text,
            normalized_text=prediction.normalized_text,
            amount=float(prediction.amount),
            transaction_class=prediction.transaction_class,
            debit_account_id=prediction.debit_account.account_id,
            debit_account_name=prediction.debit_account.account_name,
            credit_account_id=prediction.credit_account.account_id,
            credit_account_name=prediction.credit_account.account_name,
            payment_mode=prediction.payment_mode.mode,
        )

    def edit(
        self,
        prediction: TransactionPrediction,
        changes: dict[str, Any],
        *,
        edited_by: str | None = None,
        reason: str = "Human reviewer edited transaction.",
        metadata: dict[str, Any] | None = None,
        edited_at: datetime | None = None,
    ) -> TransactionEditResult:
        if not isinstance(
            prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        if not isinstance(changes, dict):
            raise TypeError(
                "changes must be a dictionary."
            )

        if not changes:
            raise ValueError(
                "At least one change is required."
            )

        if not isinstance(reason, str):
            raise TypeError(
                "reason must be a string."
            )

        if not reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )

        if len(reason) > self.config.max_reason_length:
            raise ValueError(
                "reason exceeds the configured maximum length."
            )

        if edited_by is not None:
            if not isinstance(edited_by, str):
                raise TypeError(
                    "edited_by must be a string or None."
                )

            if not edited_by.strip():
                raise ValueError(
                    "edited_by cannot be empty."
                )

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

        if len(metadata) > self.config.max_metadata_entries:
            raise ValueError(
                "metadata exceeds the configured maximum number "
                "of entries."
            )

        original = self.snapshot(prediction)

        self._validate_change_fields(changes)

        values = {
            "raw_text": original.raw_text,
            "normalized_text": original.normalized_text,
            "amount": original.amount,
            "transaction_class": original.transaction_class,
            "debit_account_id": original.debit_account_id,
            "debit_account_name": original.debit_account_name,
            "credit_account_id": original.credit_account_id,
            "credit_account_name": original.credit_account_name,
            "payment_mode": original.payment_mode,
        }

        edits: list[TransactionEdit] = []

        for field, new_value in changes.items():
            old_value = values[field]

            if old_value == new_value:
                raise ValueError(
                    f"No change supplied for field: {field}"
                )

            self._validate_field_value(
                field,
                new_value,
            )

            values[field] = new_value

            edits.append(
                TransactionEdit(
                    field=field,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

        edited = EditableTransaction(
            transaction_id=original.transaction_id,
            raw_text=values["raw_text"],
            normalized_text=values["normalized_text"],
            amount=values["amount"],
            transaction_class=values["transaction_class"],
            debit_account_id=values["debit_account_id"],
            debit_account_name=values["debit_account_name"],
            credit_account_id=values["credit_account_id"],
            credit_account_name=values["credit_account_name"],
            payment_mode=values["payment_mode"],
        )

        timestamp = edited_at or utc_now()

        if timestamp.tzinfo is None:
            raise ValueError(
                "edited_at must be timezone-aware."
            )

        return TransactionEditResult(
            original=original,
            edited=edited,
            edits=tuple(edits),
            edited_at=timestamp,
            edited_by=edited_by,
            reason=reason,
            metadata=dict(metadata),
        )

    @staticmethod
    def _validate_change_fields(
        changes: dict[str, Any],
    ) -> None:
        unsupported = set(changes) - {
            "raw_text",
            "normalized_text",
            "amount",
            "transaction_class",
            "debit_account_id",
            "debit_account_name",
            "credit_account_id",
            "credit_account_name",
            "payment_mode",
        }

        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(
                f"Unsupported editable fields: {names}"
            )

    @staticmethod
    def _validate_field_value(
        field: str,
        value: Any,
    ) -> None:
        if field == "amount":
            if not isinstance(value, (int, float)):
                raise TypeError(
                    "amount must be numeric."
                )

            if float(value) <= 0:
                raise ValueError(
                    "amount must be greater than 0."
                )

            return

        if not isinstance(value, str):
            raise TypeError(
                f"{field} must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"{field} cannot be empty."
            )

    def is_ready(self) -> bool:
        return True
