from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TransactionFeatures:
    """Deterministic features extracted from a transaction prediction."""

    transaction_id: str

    amount: float
    log_amount: float

    transaction_class: str
    payment_mode: str

    debit_account_id: str
    debit_account_name: str

    credit_account_id: str
    credit_account_name: str

    account_pair: str

    text_length: int
    word_count: int

    has_semantic_match: bool
    semantic_similarity: float

    classification_confidence: float
    debit_account_confidence: float
    credit_account_confidence: float
    debit_direction_confidence: float
    credit_direction_confidence: float
    payment_mode_confidence: float

    overall_confidence: float | None

    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if self.amount < 0:
            raise ValueError(
                "amount cannot be negative."
            )

        if not self.transaction_class.strip():
            raise ValueError(
                "transaction_class cannot be empty."
            )

        if not self.payment_mode.strip():
            raise ValueError(
                "payment_mode cannot be empty."
            )

        if not self.debit_account_id.strip():
            raise ValueError(
                "debit_account_id cannot be empty."
            )

        if not self.credit_account_id.strip():
            raise ValueError(
                "credit_account_id cannot be empty."
            )

        if self.debit_account_id == self.credit_account_id:
            raise ValueError(
                "debit and credit accounts cannot be the same."
            )

        if self.text_length < 0:
            raise ValueError(
                "text_length cannot be negative."
            )

        if self.word_count < 0:
            raise ValueError(
                "word_count cannot be negative."
            )

        for name, value in (
            (
                "semantic_similarity",
                self.semantic_similarity,
            ),
            (
                "classification_confidence",
                self.classification_confidence,
            ),
            (
                "debit_account_confidence",
                self.debit_account_confidence,
            ),
            (
                "credit_account_confidence",
                self.credit_account_confidence,
            ),
            (
                "debit_direction_confidence",
                self.debit_direction_confidence,
            ),
            (
                "credit_direction_confidence",
                self.credit_direction_confidence,
            ),
            (
                "payment_mode_confidence",
                self.payment_mode_confidence,
            ),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1."
                )

        if self.overall_confidence is not None:
            if not 0.0 <= self.overall_confidence <= 1.0:
                raise ValueError(
                    "overall_confidence must be between 0 and 1."
                )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

    @property
    def numeric_vector(self) -> tuple[float, ...]:
        """Return the numerical features used by ML models."""

        return (
            self.amount,
            self.log_amount,
            float(self.text_length),
            float(self.word_count),
            float(self.has_semantic_match),
            self.semantic_similarity,
            self.classification_confidence,
            self.debit_account_confidence,
            self.credit_account_confidence,
            self.debit_direction_confidence,
            self.credit_direction_confidence,
            self.payment_mode_confidence,
            (
                self.overall_confidence
                if self.overall_confidence is not None
                else 0.0
            ),
        )

    @property
    def categorical_features(self) -> dict[str, str]:
        """Return categorical transaction features."""

        return {
            "transaction_class": self.transaction_class,
            "payment_mode": self.payment_mode,
            "debit_account_id": self.debit_account_id,
            "credit_account_id": self.credit_account_id,
            "account_pair": self.account_pair,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize all engineered features."""

        return {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "log_amount": self.log_amount,
            "transaction_class": self.transaction_class,
            "payment_mode": self.payment_mode,
            "debit_account_id": self.debit_account_id,
            "debit_account_name": self.debit_account_name,
            "credit_account_id": self.credit_account_id,
            "credit_account_name": self.credit_account_name,
            "account_pair": self.account_pair,
            "text_length": self.text_length,
            "word_count": self.word_count,
            "has_semantic_match": self.has_semantic_match,
            "semantic_similarity": self.semantic_similarity,
            "classification_confidence": (
                self.classification_confidence
            ),
            "debit_account_confidence": (
                self.debit_account_confidence
            ),
            "credit_account_confidence": (
                self.credit_account_confidence
            ),
            "debit_direction_confidence": (
                self.debit_direction_confidence
            ),
            "credit_direction_confidence": (
                self.credit_direction_confidence
            ),
            "payment_mode_confidence": (
                self.payment_mode_confidence
            ),
            "overall_confidence": self.overall_confidence,
            "metadata": dict(self.metadata),
        }
