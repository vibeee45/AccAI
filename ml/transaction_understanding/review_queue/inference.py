from __future__ import annotations

from typing import Any

from ml.transaction_understanding.prediction import (
    TransactionPrediction,
)
from ml.transaction_understanding.confidence_routing import (
    RoutingResult,
)

from .queue import ReviewQueue
from .schemas import ReviewQueueItem


class ReviewQueueService:
    """
    Service layer for the human review queue.
    """

    def __init__(
        self,
        queue: ReviewQueue | None = None,
    ) -> None:
        self.queue = (
            queue
            if queue is not None
            else ReviewQueue()
        )

    def enqueue(
        self,
        prediction: TransactionPrediction,
        routing: RoutingResult,
        *,
        priority: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReviewQueueItem:
        return self.queue.add(
            prediction,
            routing,
            priority=priority,
            metadata=metadata,
        )

    def get(
        self,
        transaction_id: str,
    ) -> ReviewQueueItem | None:
        return self.queue.get(transaction_id)

    def pending(
        self,
    ) -> tuple[ReviewQueueItem, ...]:
        return self.queue.list_pending()

    def in_review(
        self,
    ) -> tuple[ReviewQueueItem, ...]:
        return self.queue.list_in_review()

    def start_review(
        self,
        transaction_id: str,
    ) -> ReviewQueueItem:
        return self.queue.start_review(
            transaction_id
        )

    def remove(
        self,
        transaction_id: str,
    ) -> ReviewQueueItem:
        return self.queue.remove(
            transaction_id
        )

    def is_ready(self) -> bool:
        return True
