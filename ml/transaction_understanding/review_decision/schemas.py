from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReviewDecisionResult:
    """
    Immutable human review decision.

    The result records what decision was made, who made it,
    why it was made, and when it happened.
    """

    transaction_id: str
    review_id: str
    decision: ReviewDecision
    decided_at: datetime
    decided_by: str | None
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.transaction_id, str):
            raise TypeError(
                "transaction_id must be a string."
            )

        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not isinstance(self.review_id, str):
            raise TypeError(
                "review_id must be a string."
            )

        if not self.review_id.strip():
            raise ValueError(
                "review_id cannot be empty."
            )

        if not isinstance(
            self.decision,
            ReviewDecision,
        ):
            raise TypeError(
                "decision must be ReviewDecision."
            )

        if not isinstance(
            self.decided_at,
            datetime,
        ):
            raise TypeError(
                "decided_at must be datetime."
            )

        if self.decided_at.tzinfo is None:
            raise ValueError(
                "decided_at must be timezone-aware."
            )

        if self.decided_by is not None:
            if not isinstance(self.decided_by, str):
                raise TypeError(
                    "decided_by must be a string or None."
                )

            if not self.decided_by.strip():
                raise ValueError(
                    "decided_by cannot be empty."
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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
