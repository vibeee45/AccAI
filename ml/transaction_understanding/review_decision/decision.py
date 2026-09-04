from __future__ import annotations

from datetime import datetime
from typing import Any

from ..review_queue.schemas import ReviewQueueItem
from .config import ReviewDecisionConfig
from .schemas import (
    ReviewDecision,
    ReviewDecisionResult,
    utc_now,
)


class ReviewDecisionHandler:
    """
    Handles human approval and rejection of review-queue items.

    This component records the decision only. It does not:
    - mutate the original AI prediction
    - persist corrections
    - create accounting entries
    - write to PostgreSQL

    Those responsibilities belong to later phases.
    """

    def __init__(
        self,
        config: ReviewDecisionConfig | None = None,
    ) -> None:
        self.config = config or ReviewDecisionConfig()

    def approve(
        self,
        item: ReviewQueueItem,
        *,
        decided_by: str | None = None,
        reason: str = "Transaction approved by human reviewer.",
        metadata: dict[str, Any] | None = None,
        decided_at: datetime | None = None,
    ) -> ReviewDecisionResult:
        return self.decide(
            item,
            ReviewDecision.APPROVED,
            decided_by=decided_by,
            reason=reason,
            metadata=metadata,
            decided_at=decided_at,
        )

    def reject(
        self,
        item: ReviewQueueItem,
        *,
        decided_by: str | None = None,
        reason: str = "Transaction rejected by human reviewer.",
        metadata: dict[str, Any] | None = None,
        decided_at: datetime | None = None,
    ) -> ReviewDecisionResult:
        return self.decide(
            item,
            ReviewDecision.REJECTED,
            decided_by=decided_by,
            reason=reason,
            metadata=metadata,
            decided_at=decided_at,
        )

    def decide(
        self,
        item: ReviewQueueItem,
        decision: ReviewDecision,
        *,
        decided_by: str | None = None,
        reason: str = "Human review decision.",
        metadata: dict[str, Any] | None = None,
        decided_at: datetime | None = None,
    ) -> ReviewDecisionResult:
        if not isinstance(
            item,
            ReviewQueueItem,
        ):
            raise TypeError(
                "item must be ReviewQueueItem."
            )

        if not isinstance(
            decision,
            ReviewDecision,
        ):
            raise TypeError(
                "decision must be ReviewDecision."
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

        if decided_by is not None:
            if not isinstance(decided_by, str):
                raise TypeError(
                    "decided_by must be a string or None."
                )

            if not decided_by.strip():
                raise ValueError(
                    "decided_by cannot be empty."
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

        timestamp = decided_at or utc_now()

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "decided_at must be datetime."
            )

        if timestamp.tzinfo is None:
            raise ValueError(
                "decided_at must be timezone-aware."
            )

        return ReviewDecisionResult(
            transaction_id=item.transaction_id,
            review_id=item.review_id,
            decision=decision,
            decided_at=timestamp,
            decided_by=decided_by,
            reason=reason,
            metadata=dict(metadata),
        )

    def is_ready(self) -> bool:
        return True
