from __future__ import annotations

from typing import Iterable

from ml.transaction_understanding.prediction import (
    TransactionPrediction,
)
from ml.transaction_understanding.confidence_routing import (
    RoutingDecision,
    RoutingResult,
)

from .config import ReviewQueueConfig
from .schemas import (
    ReviewQueueItem,
    ReviewQueueStats,
    ReviewStatus,
    utc_now,
)


class ReviewQueue:
    """
    In-memory queue for transactions requiring
    human review.

    Persistence is intentionally outside this subset.
    """

    def __init__(
        self,
        config: ReviewQueueConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else ReviewQueueConfig()
        )

        self._items: dict[
            str,
            ReviewQueueItem,
        ] = {}

    def add(
        self,
        prediction: TransactionPrediction,
        routing: RoutingResult,
        *,
        priority: int | None = None,
        metadata: dict | None = None,
    ) -> ReviewQueueItem:
        if not isinstance(
            prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        if not isinstance(
            routing,
            RoutingResult,
        ):
            raise TypeError(
                "routing must be RoutingResult."
            )

        if (
            routing.decision
            != RoutingDecision.HUMAN_REVIEW
        ):
            raise ValueError(
                "Only HUMAN_REVIEW transactions "
                "can be added to the review queue."
            )

        transaction_id = prediction.transaction_id

        if transaction_id in self._items:
            raise ValueError(
                "Transaction is already in the review queue."
            )

        if len(self._items) >= self.config.max_queue_size:
            raise OverflowError(
                "Review queue has reached its maximum size."
            )

        item_priority = (
            self.config.default_priority
            if priority is None
            else priority
        )

        if item_priority < 0:
            raise ValueError(
                "priority cannot be negative."
            )

        item = ReviewQueueItem(
            review_id=f"REVIEW-{transaction_id}",
            transaction_id=transaction_id,
            prediction=prediction,
            routing=routing,
            status=ReviewStatus.PENDING,
            priority=item_priority,
            reason=routing.reason,
            created_at=utc_now(),
            metadata=dict(metadata or {}),
        )

        self._items[transaction_id] = item

        return item

    def get(
        self,
        transaction_id: str,
    ) -> ReviewQueueItem | None:
        return self._items.get(transaction_id)

    def list_pending(
        self,
    ) -> tuple[ReviewQueueItem, ...]:
        return tuple(
            sorted(
                (
                    item
                    for item in self._items.values()
                    if item.status == ReviewStatus.PENDING
                ),
                key=lambda item: (
                    -item.priority,
                    item.created_at,
                ),
            )
        )

    def list_in_review(
        self,
    ) -> tuple[ReviewQueueItem, ...]:
        return tuple(
            sorted(
                (
                    item
                    for item in self._items.values()
                    if item.status == ReviewStatus.IN_REVIEW
                ),
                key=lambda item: (
                    -item.priority,
                    item.created_at,
                ),
            )
        )

    def list_all(
        self,
    ) -> tuple[ReviewQueueItem, ...]:
        return tuple(
            sorted(
                self._items.values(),
                key=lambda item: (
                    -item.priority,
                    item.created_at,
                ),
            )
        )

    def start_review(
        self,
        transaction_id: str,
    ) -> ReviewQueueItem:
        item = self.get(transaction_id)

        if item is None:
            raise KeyError(
                "Transaction is not in the review queue."
            )

        if item.status != ReviewStatus.PENDING:
            raise ValueError(
                "Only pending transactions can be started."
            )

        updated = ReviewQueueItem(
            review_id=item.review_id,
            transaction_id=item.transaction_id,
            prediction=item.prediction,
            routing=item.routing,
            status=ReviewStatus.IN_REVIEW,
            priority=item.priority,
            reason=item.reason,
            created_at=item.created_at,
            metadata=dict(item.metadata),
        )

        self._items[transaction_id] = updated

        return updated

    def remove(
        self,
        transaction_id: str,
    ) -> ReviewQueueItem:
        item = self._items.pop(
            transaction_id,
            None,
        )

        if item is None:
            raise KeyError(
                "Transaction is not in the review queue."
            )

        return item

    def contains(
        self,
        transaction_id: str,
    ) -> bool:
        return transaction_id in self._items

    def __len__(self) -> int:
        return len(self._items)

    def stats(self) -> ReviewQueueStats:
        pending = sum(
            item.status == ReviewStatus.PENDING
            for item in self._items.values()
        )

        in_review = sum(
            item.status == ReviewStatus.IN_REVIEW
            for item in self._items.values()
        )

        return ReviewQueueStats(
            total=len(self._items),
            pending=pending,
            in_review=in_review,
        )

    def add_many(
        self,
        items: Iterable[
            tuple[
                TransactionPrediction,
                RoutingResult,
            ]
        ],
    ) -> tuple[ReviewQueueItem, ...]:
        return tuple(
            self.add(
                prediction,
                routing,
            )
            for prediction, routing in items
        )
