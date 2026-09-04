from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..correction_storage.schemas import CorrectionRecord, CorrectionStatus


from enum import Enum


class FeedbackLabel(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class FeedbackExample:
    feedback_id: str
    transaction_id: str
    review_id: str
    original_text: str
    corrected_text: str
    original_transaction_class: str
    corrected_transaction_class: str
    original_debit_account_id: str
    corrected_debit_account_id: str
    original_debit_account_name: str
    corrected_debit_account_name: str
    original_credit_account_id: str
    corrected_credit_account_id: str
    original_credit_account_name: str
    corrected_credit_account_name: str
    original_payment_mode: str
    corrected_payment_mode: str
    original_amount: float | None
    corrected_amount: float | None
    changed_fields: tuple[str, ...]
    label: str
    reviewer: str
    reason: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.feedback_id:
            raise ValueError("feedback_id cannot be empty")
        if not self.transaction_id:
            raise ValueError("transaction_id cannot be empty")
        if not self.review_id:
            raise ValueError("review_id cannot be empty")
        if self.label not in (
            FeedbackLabel.APPROVED,
            FeedbackLabel.REJECTED,
        ):
            raise ValueError("invalid feedback label")
        if not isinstance(self.changed_fields, tuple):
            raise TypeError("changed_fields must be a tuple")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dict")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

    @property
    def has_changes(self) -> bool:
        return bool(self.changed_fields)

    @property
    def is_approved(self) -> bool:
        return self.label == FeedbackLabel.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.label == FeedbackLabel.REJECTED

    def to_training_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "transaction_id": self.transaction_id,
            "review_id": self.review_id,
            "text": self.corrected_text,
            "transaction_class": self.corrected_transaction_class,
            "debit_account_id": self.corrected_debit_account_id,
            "debit_account_name": self.corrected_debit_account_name,
            "credit_account_id": self.corrected_credit_account_id,
            "credit_account_name": self.corrected_credit_account_name,
            "payment_mode": self.corrected_payment_mode,
            "amount": self.corrected_amount,
            "label": self.label,
            "changed_fields": list(self.changed_fields),
        }


@dataclass(frozen=True)
class FeedbackDataset:
    examples: tuple[FeedbackExample, ...]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.examples, tuple):
            raise TypeError("examples must be a tuple")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dict")

        ids = [example.feedback_id for example in self.examples]
        if len(ids) != len(set(ids)):
            raise ValueError("feedback IDs must be unique")

    @property
    def count(self) -> int:
        return len(self.examples)

    @property
    def approved_count(self) -> int:
        return sum(example.is_approved for example in self.examples)

    @property
    def rejected_count(self) -> int:
        return sum(example.is_rejected for example in self.examples)

    @property
    def corrected_count(self) -> int:
        return sum(example.has_changes for example in self.examples)

    def to_training_records(self) -> list[dict[str, Any]]:
        return [
            example.to_training_dict()
            for example in self.examples
        ]
