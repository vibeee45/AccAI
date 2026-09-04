from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StructuredAccount:
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
class StructuredDirection:
    account_id: str
    direction: str
    confidence: float
    reason: str | None = None
    requires_review: bool = False

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
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

        if self.reason is not None:
            if not self.reason.strip():
                raise ValueError(
                    "reason cannot be empty when provided."
                )


@dataclass(frozen=True)
class StructuredPaymentMode:
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
class StructuredSemanticMatch:
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
class StructuredConfidence:
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
class StructuredTransaction:
    transaction_id: str
    raw_text: str
    normalized_text: str
    amount: float | None
    transaction_class: str
    classification_confidence: float

    debit_account: StructuredAccount
    credit_account: StructuredAccount

    debit: StructuredDirection
    credit: StructuredDirection

    payment_mode: StructuredPaymentMode

    confidence: StructuredConfidence | None = None

    entities: tuple[Any, ...] = field(
        default_factory=tuple
    )

    semantic_matches: tuple[
        StructuredSemanticMatch,
        ...
    ] = field(
        default_factory=tuple
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    status: str = "success"

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
            StructuredAccount,
        ):
            raise TypeError(
                "debit_account must be StructuredAccount."
            )

        if not isinstance(
            self.credit_account,
            StructuredAccount,
        ):
            raise TypeError(
                "credit_account must be StructuredAccount."
            )

        if (
            self.debit_account.account_id
            == self.credit_account.account_id
        ):
            raise ValueError(
                "debit and credit accounts "
                "cannot be the same."
            )

        if self.debit.direction != "debit":
            raise ValueError(
                "debit must have direction='debit'."
            )

        if self.credit.direction != "credit":
            raise ValueError(
                "credit must have direction='credit'."
            )

        if not isinstance(
            self.payment_mode,
            StructuredPaymentMode,
        ):
            raise TypeError(
                "payment_mode must be StructuredPaymentMode."
            )

        if self.confidence is not None:
            if not isinstance(
                self.confidence,
                StructuredConfidence,
            ):
                raise TypeError(
                    "confidence must be StructuredConfidence."
                )

        if not isinstance(
            self.entities,
            tuple,
        ):
            raise TypeError(
                "entities must be a tuple."
            )

        if not isinstance(
            self.semantic_matches,
            tuple,
        ):
            raise TypeError(
                "semantic_matches must be a tuple."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )


@dataclass(frozen=True)
class StructuredBatch:
    transactions: tuple[
        StructuredTransaction,
        ...
    ]

    def __post_init__(self) -> None:
        if not isinstance(
            self.transactions,
            tuple,
        ):
            raise TypeError(
                "transactions must be a tuple."
            )

        ids = [
            transaction.transaction_id
            for transaction in self.transactions
        ]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Structured batch contains "
                "duplicate transaction IDs."
            )

    @property
    def count(self) -> int:
        return len(self.transactions)
