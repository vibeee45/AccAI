from decimal import Decimal

import pytest

from ml.transaction_understanding.prediction import (
    PredictionAccount,
    PredictionConfidence,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionStatus,
    TransactionPrediction,
)
from ml.transaction_understanding.confidence_routing import (
    ConfidenceRouter,
    RoutingDecision,
)
from ml.transaction_understanding.debit_credit import (
    DebitCredit,
)
from ml.transaction_understanding.review_queue import (
    ReviewQueue,
    ReviewQueueConfig,
    ReviewQueueService,
    ReviewStatus,
)


def make_prediction(
    transaction_id="txn-review-001",
    confidence=0.65,
):
    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="Received cash sales of Rs 5000",
        normalized_text="received cash sales of rs 5000",
        amount=Decimal("5000"),
        transaction_class="sales",
        classification_confidence=confidence,
        debit_account=PredictionAccount(
            account_id="cash",
            account_name="Cash",
            confidence=confidence,
        ),
        credit_account=PredictionAccount(
            account_id="sales",
            account_name="Sales",
            confidence=confidence,
        ),
        debit_prediction=PredictionDirection(
            account_id="cash",
            account_name="Cash",
            direction=DebitCredit.DEBIT,
            confidence=confidence,
            reason="Cash received.",
            requires_review=True,
        ),
        credit_prediction=PredictionDirection(
            account_id="sales",
            account_name="Sales",
            direction=DebitCredit.CREDIT,
            confidence=confidence,
            reason="Sales credited.",
            requires_review=True,
        ),
        payment_mode=PredictionPaymentMode(
            mode="cash",
            confidence=confidence,
            requires_review=True,
        ),
        confidence=PredictionConfidence(
            overall=confidence,
            requires_review=True,
            reason="Confidence requires human review.",
        ),
        status=PredictionStatus.REVIEW_REQUIRED,
    )


def make_review_routing(confidence=0.65):
    return ConfidenceRouter().route(
        confidence,
        requires_review=False,
    )


def test_add_human_review_transaction():
    queue = ReviewQueue()

    prediction = make_prediction()
    routing = make_review_routing()

    item = queue.add(
        prediction,
        routing,
    )

    assert item.transaction_id == "txn-review-001"
    assert item.status == ReviewStatus.PENDING
    assert item.prediction is prediction
    assert item.routing is routing
    assert queue.contains("txn-review-001")


def test_rejects_non_human_review_routing():
    queue = ReviewQueue()

    prediction = make_prediction(
        confidence=0.95,
    )

    routing = ConfidenceRouter().route(
        0.95,
    )

    assert routing.decision == RoutingDecision.AUTO_PROCESS

    with pytest.raises(ValueError):
        queue.add(
            prediction,
            routing,
        )


def test_get_returns_queue_item():
    queue = ReviewQueue()

    prediction = make_prediction()
    routing = make_review_routing()

    queue.add(
        prediction,
        routing,
    )

    item = queue.get(
        "txn-review-001"
    )

    assert item is not None
    assert item.transaction_id == "txn-review-001"


def test_get_unknown_transaction_returns_none():
    queue = ReviewQueue()

    assert queue.get(
        "does-not-exist"
    ) is None


def test_duplicate_transaction_is_rejected():
    queue = ReviewQueue()

    prediction = make_prediction()
    routing = make_review_routing()

    queue.add(
        prediction,
        routing,
    )

    with pytest.raises(ValueError):
        queue.add(
            prediction,
            routing,
        )


def test_pending_queue_returns_pending_items():
    queue = ReviewQueue()

    queue.add(
        make_prediction("txn-review-001"),
        make_review_routing(),
    )

    queue.add(
        make_prediction("txn-review-002"),
        make_review_routing(),
    )

    pending = queue.list_pending()

    assert len(pending) == 2
    assert all(
        item.status == ReviewStatus.PENDING
        for item in pending
    )


def test_priority_orders_pending_items():
    queue = ReviewQueue()

    queue.add(
        make_prediction("txn-low"),
        make_review_routing(),
        priority=1,
    )

    queue.add(
        make_prediction("txn-high"),
        make_review_routing(),
        priority=10,
    )

    pending = queue.list_pending()

    assert pending[0].transaction_id == "txn-high"
    assert pending[1].transaction_id == "txn-low"


def test_start_review_changes_status():
    queue = ReviewQueue()

    queue.add(
        make_prediction(),
        make_review_routing(),
    )

    item = queue.start_review(
        "txn-review-001"
    )

    assert item.status == ReviewStatus.IN_REVIEW

    stored = queue.get(
        "txn-review-001"
    )

    assert stored is not None
    assert stored.status == ReviewStatus.IN_REVIEW


def test_only_pending_items_can_start_review():
    queue = ReviewQueue()

    queue.add(
        make_prediction(),
        make_review_routing(),
    )

    queue.start_review(
        "txn-review-001"
    )

    with pytest.raises(ValueError):
        queue.start_review(
            "txn-review-001"
        )


def test_start_review_unknown_transaction_fails():
    queue = ReviewQueue()

    with pytest.raises(KeyError):
        queue.start_review(
            "does-not-exist"
        )


def test_remove_returns_item():
    queue = ReviewQueue()

    queue.add(
        make_prediction(),
        make_review_routing(),
    )

    removed = queue.remove(
        "txn-review-001"
    )

    assert removed.transaction_id == "txn-review-001"
    assert not queue.contains(
        "txn-review-001"
    )


def test_remove_unknown_transaction_fails():
    queue = ReviewQueue()

    with pytest.raises(KeyError):
        queue.remove(
            "does-not-exist"
        )


def test_queue_statistics():
    queue = ReviewQueue()

    queue.add(
        make_prediction("txn-review-001"),
        make_review_routing(),
    )

    queue.add(
        make_prediction("txn-review-002"),
        make_review_routing(),
    )

    queue.start_review(
        "txn-review-002"
    )

    stats = queue.stats()

    assert stats.total == 2
    assert stats.pending == 1
    assert stats.in_review == 1


def test_max_queue_size():
    queue = ReviewQueue(
        ReviewQueueConfig(
            max_queue_size=1,
        )
    )

    queue.add(
        make_prediction("txn-review-001"),
        make_review_routing(),
    )

    with pytest.raises(OverflowError):
        queue.add(
            make_prediction("txn-review-002"),
            make_review_routing(),
        )


def test_negative_priority_is_rejected():
    queue = ReviewQueue()

    with pytest.raises(ValueError):
        queue.add(
            make_prediction(),
            make_review_routing(),
            priority=-1,
        )


def test_metadata_is_preserved():
    queue = ReviewQueue()

    item = queue.add(
        make_prediction(),
        make_review_routing(),
        metadata={
            "source": "ai",
            "model_version": "v1",
        },
    )

    assert item.metadata["source"] == "ai"
    assert item.metadata["model_version"] == "v1"


def test_service_enqueue_and_get():
    service = ReviewQueueService()

    prediction = make_prediction(
        "txn-service-001"
    )

    routing = make_review_routing()

    item = service.enqueue(
        prediction,
        routing,
    )

    assert item.transaction_id == "txn-service-001"

    stored = service.get(
        "txn-service-001"
    )

    assert stored is not None
    assert stored.transaction_id == "txn-service-001"


def test_service_is_ready():
    service = ReviewQueueService()

    assert service.is_ready() is True


def test_add_many():
    queue = ReviewQueue()

    items = queue.add_many(
        [
            (
                make_prediction("txn-batch-001"),
                make_review_routing(),
            ),
            (
                make_prediction("txn-batch-002"),
                make_review_routing(),
            ),
        ]
    )

    assert len(items) == 2
    assert len(queue) == 2


def test_in_review_listing():
    queue = ReviewQueue()

    queue.add(
        make_prediction("txn-review-001"),
        make_review_routing(),
    )

    queue.add(
        make_prediction("txn-review-002"),
        make_review_routing(),
    )

    queue.start_review(
        "txn-review-002"
    )

    items = queue.list_in_review()

    assert len(items) == 1
    assert items[0].transaction_id == "txn-review-002"


def test_all_listing_contains_pending_and_in_review():
    queue = ReviewQueue()

    queue.add(
        make_prediction("txn-review-001"),
        make_review_routing(),
    )

    queue.add(
        make_prediction("txn-review-002"),
        make_review_routing(),
    )

    queue.start_review(
        "txn-review-002"
    )

    items = queue.list_all()

    assert len(items) == 2

    statuses = {
        item.status
        for item in items
    }

    assert ReviewStatus.PENDING in statuses
    assert ReviewStatus.IN_REVIEW in statuses
