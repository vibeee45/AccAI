from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PredictionStatus(str, Enum):
    SUCCESS = "success"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"


@dataclass(frozen=True)
class PredictionAccount:
    account_id: str
    account_name: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name.strip():
            raise ValueError(
                "account_name cannot be empty."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )


@dataclass(frozen=True)
class PredictionDirection:
    account_id: str
    account_name: str
    direction: str
    confidence: float
    reason: str
    requires_review: bool

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name.strip():
            raise ValueError(
                "account_name cannot be empty."
            )

        if self.direction not in {
            "debit",
            "credit",
        }:
            raise ValueError(
                "direction must be 'debit' or 'credit'."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )


@dataclass(frozen=True)
class PredictionPaymentMode:
    mode: str
    confidence: float
    requires_review: bool

    def __post_init__(self) -> None:
        if not self.mode.strip():
            raise ValueError(
                "mode cannot be empty."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )


@dataclass(frozen=True)
class PredictionSemanticMatch:
    candidate_id: str
    candidate_text: str
    similarity: float

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError(
                "candidate_id cannot be empty."
            )

        if not self.candidate_text.strip():
            raise ValueError(
                "candidate_text cannot be empty."
            )

        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError(
                "similarity must be between 0 and 1."
            )


@dataclass(frozen=True)
class PredictionConfidence:
    overall: float
    requires_review: bool
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall <= 1.0:
            raise ValueError(
                "overall confidence must be between 0 and 1."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )


@dataclass(frozen=True)
class TransactionPrediction:
    transaction_id: str
    raw_text: str
    normalized_text: str
    amount: float | None
    transaction_class: str
    classification_confidence: float
    debit_account: PredictionAccount
    credit_account: PredictionAccount
    debit_prediction: PredictionDirection
    credit_prediction: PredictionDirection
    payment_mode: PredictionPaymentMode
    semantic_matches: tuple[
        PredictionSemanticMatch,
        ...
    ] = field(default_factory=tuple)
    confidence: PredictionConfidence | None = None
    entities: tuple[Any, ...] = field(
        default_factory=tuple
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    status: PredictionStatus = (
        PredictionStatus.SUCCESS
    )

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not self.raw_text.strip():
            raise ValueError(
                "raw_text cannot be empty."
            )

        if not self.normalized_text.strip():
            raise ValueError(
                "normalized_text cannot be empty."
            )

        if self.amount is not None:
            if self.amount < 0:
                raise ValueError(
                    "amount cannot be negative."
                )

        if not self.transaction_class.strip():
            raise ValueError(
                "transaction_class cannot be empty."
            )

        if not 0.0 <= self.classification_confidence <= 1.0:
            raise ValueError(
                "classification_confidence must be between 0 and 1."
            )

        if not isinstance(
            self.debit_account,
            PredictionAccount,
        ):
            raise TypeError(
                "debit_account must be PredictionAccount."
            )

        if not isinstance(
            self.credit_account,
            PredictionAccount,
        ):
            raise TypeError(
                "credit_account must be PredictionAccount."
            )

        if (
            self.debit_account.account_id
            == self.credit_account.account_id
        ):
            raise ValueError(
                "debit and credit accounts "
                "cannot be the same."
            )

        if not isinstance(
            self.debit_prediction,
            PredictionDirection,
        ):
            raise TypeError(
                "debit_prediction must be "
                "PredictionDirection."
            )

        if not isinstance(
            self.credit_prediction,
            PredictionDirection,
        ):
            raise TypeError(
                "credit_prediction must be "
                "PredictionDirection."
            )

        if self.debit_prediction.direction != "debit":
            raise ValueError(
                "debit_prediction must have "
                "direction='debit'."
            )

        if self.credit_prediction.direction != "credit":
            raise ValueError(
                "credit_prediction must have "
                "direction='credit'."
            )

        if not isinstance(
            self.payment_mode,
            PredictionPaymentMode,
        ):
            raise TypeError(
                "payment_mode must be "
                "PredictionPaymentMode."
            )

        if self.confidence is not None:
            if not isinstance(
                self.confidence,
                PredictionConfidence,
            ):
                raise TypeError(
                    "confidence must be "
                    "PredictionConfidence."
                )

        if not isinstance(
            self.semantic_matches,
            tuple,
        ):
            raise TypeError(
                "semantic_matches must be a tuple."
            )

        if not isinstance(
            self.entities,
            tuple,
        ):
            raise TypeError(
                "entities must be a tuple."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )


@dataclass(frozen=True)
class PredictionBatch:
    predictions: tuple[
        TransactionPrediction,
        ...
    ]

    def __post_init__(self) -> None:
        if not isinstance(
            self.predictions,
            tuple,
        ):
            raise TypeError(
                "predictions must be a tuple."
            )

        transaction_ids = [
            prediction.transaction_id
            for prediction in self.predictions
        ]

        if len(transaction_ids) != len(
            set(transaction_ids)
        ):
            raise ValueError(
                "Prediction batch contains "
                "duplicate transaction IDs."
            )

    @property
    def count(self) -> int:
        return len(self.predictions)

    @property
    def review_required_count(self) -> int:
        return sum(
            prediction.status
            == PredictionStatus.REVIEW_REQUIRED
            for prediction in self.predictions
        )

    @property
    def failed_count(self) -> int:
        return sum(
            prediction.status
            == PredictionStatus.FAILED
            for prediction in self.predictions
        )
