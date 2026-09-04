from __future__ import annotations

from datetime import datetime
from typing import Any

from ..review_queue.schemas import ReviewQueueItem
from .config import ReviewDecisionConfig
from .decision import ReviewDecisionHandler
from .schemas import (
    ReviewDecision,
    ReviewDecisionResult,
)


class ReviewDecisionService:
    """
    Service layer for human approval/rejection.
    """

    def __init__(
        self,
        handler: ReviewDecisionHandler | None = None,
        config: ReviewDecisionConfig | None = None,
    ) -> None:
        if handler is not None and config is not None:
            raise ValueError(
                "Provide either handler or config, not both."
            )

        self.handler = handler or ReviewDecisionHandler(config)

    def approve(
        self,
        item: ReviewQueueItem,
        *,
        decided_by: str | None = None,
        reason: str = "Transaction approved by human reviewer.",
        metadata: dict[str, Any] | None = None,
        decided_at: datetime | None = None,
    ) -> ReviewDecisionResult:
        return self.handler.approve(
            item,
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
        return self.handler.reject(
            item,
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
        return self.handler.decide(
            item,
            decision,
            decided_by=decided_by,
            reason=reason,
            metadata=metadata,
            decided_at=decided_at,
        )

    def is_ready(self) -> bool:
        return self.handler.is_ready()
