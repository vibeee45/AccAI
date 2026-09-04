from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ml.transaction_understanding.prediction import (
    TransactionPrediction,
)
from ml.transaction_understanding.confidence_routing import (
    RoutingResult,
)


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"


@dataclass(frozen=True)
class ReviewQueueItem:
    review_id: str
    transaction_id: str
    prediction: TransactionPrediction
    routing: RoutingResult
    status: ReviewStatus
    priority: int
    reason: str
    created_at: datetime
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.review_id.strip():
            raise ValueError(
                "review_id cannot be empty."
            )

        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not isinstance(
            self.prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        if not isinstance(
            self.routing,
            RoutingResult,
        ):
            raise TypeError(
                "routing must be RoutingResult."
            )

        if self.routing.decision.value != "human_review":
            raise ValueError(
                "Review queue items require HUMAN_REVIEW routing."
            )

        if (
            self.prediction.transaction_id
            != self.transaction_id
        ):
            raise ValueError(
                "transaction_id must match prediction."
            )

        if not isinstance(
            self.status,
            ReviewStatus,
        ):
            raise TypeError(
                "status must be ReviewStatus."
            )

        if self.priority < 0:
            raise ValueError(
                "priority cannot be negative."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )

        if not isinstance(
            self.created_at,
            datetime,
        ):
            raise TypeError(
                "created_at must be datetime."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )


@dataclass(frozen=True)
class ReviewQueueStats:
    total: int
    pending: int
    in_review: int

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError(
                "total cannot be negative."
            )

        if self.pending < 0:
            raise ValueError(
                "pending cannot be negative."
            )

        if self.in_review < 0:
            raise ValueError(
                "in_review cannot be negative."
            )

        if self.total != self.pending + self.in_review:
            raise ValueError(
                "total must equal pending + in_review."
            )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
