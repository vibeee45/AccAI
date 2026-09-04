from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ml.transaction_understanding.confidence_routing.schemas import (
    RoutingDecision,
    RoutingResult,
)
from ml.transaction_understanding.prediction.schemas import (
    PredictionAccount,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionStatus,
    TransactionPrediction,
)
from ml.transaction_understanding.review_decision.config import (
    ReviewDecisionConfig,
)
from ml.transaction_understanding.review_decision.decision import (
    ReviewDecisionHandler,
)
from ml.transaction_understanding.review_decision.inference import (
    ReviewDecisionService,
)
from ml.transaction_understanding.review_decision.schemas import (
    ReviewDecision,
    ReviewDecisionResult,
)
from ml.transaction_understanding.review_queue.schemas import (
    ReviewQueueItem,
    ReviewStatus,
)


def make_prediction() -> TransactionPrediction:
    debit_account = PredictionAccount(
        account_id="rent_expense",
        account_name="Rent Expense",
        confidence=0.60,
    )

    credit_account = PredictionAccount(
        account_id="bank",
        account_name="Bank",
        confidence=0.70,
    )

    debit_prediction = PredictionDirection(
        account_id="rent_expense",
        account_name="Rent Expense",
        direction="debit",
        confidence=0.60,
        reason="Expense account is debited.",
        requires_review=True,
    )

    credit_prediction = PredictionDirection(
        account_id="bank",
        account_name="Bank",
        direction="credit",
        confidence=0.70,
        reason="Bank account is credited.",
        requires_review=True,
    )

    payment_mode = PredictionPaymentMode(
        mode="NEFT",
        confidence=0.60,
        requires_review=True,
    )

    return TransactionPrediction(
        transaction_id="TX-001",
        raw_text="Paid office rent of Rs 5000 by NEFT.",
        normalized_text="paid office rent of rs 5000 by neft.",
        amount=5000.0,
        transaction_class="rent",
        classification_confidence=0.60,
        debit_account=debit_account,
        credit_account=credit_account,
        debit_prediction=debit_prediction,
        credit_prediction=credit_prediction,
        payment_mode=payment_mode,
        status=PredictionStatus.REVIEW_REQUIRED,
    )


def make_item() -> ReviewQueueItem:
    prediction = make_prediction()

    routing = RoutingResult(
        decision=RoutingDecision.HUMAN_REVIEW,
        confidence=0.60,
        reason="Confidence below automatic processing threshold.",
        requires_review=True,
    )

    return ReviewQueueItem(
        review_id="REVIEW-TX-001",
        transaction_id="TX-001",
        prediction=prediction,
        routing=routing,
        status=ReviewStatus.IN_REVIEW,
        priority=1,
        reason="Low confidence transaction.",
        created_at=datetime(
            2026,
            9,
            4,
            20,
            0,
            tzinfo=timezone.utc,
        ),
        metadata={
            "source": "test",
        },
    )


def test_config_defaults():
    config = ReviewDecisionConfig()

    assert config.max_reason_length == 500
    assert config.max_metadata_entries == 100


def test_config_rejects_invalid_reason_limit():
    with pytest.raises(ValueError):
        ReviewDecisionConfig(
            max_reason_length=0,
        )


def test_config_rejects_invalid_metadata_limit():
    with pytest.raises(ValueError):
        ReviewDecisionConfig(
            max_metadata_entries=0,
        )


def test_approve():
    handler = ReviewDecisionHandler()

    result = handler.approve(
        make_item(),
        decided_by="reviewer-1",
        reason="Reviewed and approved.",
    )

    assert isinstance(
        result,
        ReviewDecisionResult,
    )

    assert result.transaction_id == "TX-001"
    assert result.review_id == "REVIEW-TX-001"
    assert result.decision == ReviewDecision.APPROVED
    assert result.decided_by == "reviewer-1"
    assert result.reason == "Reviewed and approved."


def test_reject():
    handler = ReviewDecisionHandler()

    result = handler.reject(
        make_item(),
        decided_by="reviewer-2",
        reason="Account mapping is incorrect.",
    )

    assert result.decision == ReviewDecision.REJECTED
    assert result.decided_by == "reviewer-2"
    assert result.reason == "Account mapping is incorrect."


def test_generic_decide_approve():
    handler = ReviewDecisionHandler()

    result = handler.decide(
        make_item(),
        ReviewDecision.APPROVED,
        reason="Generic approval.",
    )

    assert result.decision == ReviewDecision.APPROVED


def test_generic_decide_reject():
    handler = ReviewDecisionHandler()

    result = handler.decide(
        make_item(),
        ReviewDecision.REJECTED,
        reason="Generic rejection.",
    )

    assert result.decision == ReviewDecision.REJECTED


def test_decision_preserves_transaction_identity():
    handler = ReviewDecisionHandler()

    result = handler.approve(
        make_item(),
    )

    assert result.transaction_id == "TX-001"
    assert result.review_id == "REVIEW-TX-001"


def test_decision_records_timestamp():
    handler = ReviewDecisionHandler()

    timestamp = datetime(
        2026,
        9,
        4,
        21,
        30,
        tzinfo=timezone.utc,
    )

    result = handler.approve(
        make_item(),
        decided_at=timestamp,
    )

    assert result.decided_at == timestamp


def test_decision_rejects_naive_timestamp():
    handler = ReviewDecisionHandler()

    timestamp = datetime(
        2026,
        9,
        4,
        21,
        30,
    )

    with pytest.raises(ValueError):
        handler.approve(
            make_item(),
            decided_at=timestamp,
        )


def test_decision_records_metadata():
    handler = ReviewDecisionHandler()

    result = handler.approve(
        make_item(),
        metadata={
            "screen": "review",
            "source": "human",
        },
    )

    assert result.metadata["screen"] == "review"
    assert result.metadata["source"] == "human"


def test_decision_rejects_empty_reason():
    handler = ReviewDecisionHandler()

    with pytest.raises(ValueError):
        handler.approve(
            make_item(),
            reason="",
        )


def test_decision_rejects_long_reason():
    handler = ReviewDecisionHandler(
        ReviewDecisionConfig(
            max_reason_length=10,
        )
    )

    with pytest.raises(ValueError):
        handler.approve(
            make_item(),
            reason="This reason is too long.",
        )


def test_decision_rejects_empty_reviewer():
    handler = ReviewDecisionHandler()

    with pytest.raises(ValueError):
        handler.approve(
            make_item(),
            decided_by="",
        )


def test_decision_allows_no_reviewer():
    handler = ReviewDecisionHandler()

    result = handler.approve(
        make_item(),
        decided_by=None,
    )

    assert result.decided_by is None


def test_decision_rejects_invalid_item():
    handler = ReviewDecisionHandler()

    with pytest.raises(TypeError):
        handler.approve(
            "invalid",
        )


def test_decision_rejects_invalid_decision():
    handler = ReviewDecisionHandler()

    with pytest.raises(TypeError):
        handler.decide(
            make_item(),
            "approved",
        )


def test_decision_does_not_mutate_prediction():
    item = make_item()

    original_amount = item.prediction.amount
    original_status = item.prediction.status

    handler = ReviewDecisionHandler()

    handler.approve(
        item,
        reason="Approved after review.",
    )

    assert item.prediction.amount == original_amount
    assert item.prediction.status == original_status


def test_approval_and_rejection_are_distinct():
    handler = ReviewDecisionHandler()

    approved = handler.approve(
        make_item(),
    )

    rejected = handler.reject(
        make_item(),
    )

    assert approved.decision != rejected.decision
    assert approved.decision == ReviewDecision.APPROVED
    assert rejected.decision == ReviewDecision.REJECTED


def test_service_approve():
    service = ReviewDecisionService()

    result = service.approve(
        make_item(),
        decided_by="reviewer",
        reason="Approved.",
    )

    assert result.decision == ReviewDecision.APPROVED


def test_service_reject():
    service = ReviewDecisionService()

    result = service.reject(
        make_item(),
        decided_by="reviewer",
        reason="Rejected.",
    )

    assert result.decision == ReviewDecision.REJECTED


def test_service_generic_decide():
    service = ReviewDecisionService()

    result = service.decide(
        make_item(),
        ReviewDecision.APPROVED,
        reason="Approved through service.",
    )

    assert result.decision == ReviewDecision.APPROVED


def test_service_is_ready():
    service = ReviewDecisionService()

    assert service.is_ready() is True


def test_service_rejects_handler_and_config_together():
    handler = ReviewDecisionHandler()

    with pytest.raises(ValueError):
        ReviewDecisionService(
            handler=handler,
            config=ReviewDecisionConfig(),
        )


def test_result_schema_validation():
    timestamp = datetime.now(timezone.utc)

    result = ReviewDecisionResult(
        transaction_id="TX-001",
        review_id="REVIEW-TX-001",
        decision=ReviewDecision.APPROVED,
        decided_at=timestamp,
        decided_by="reviewer",
        reason="Approved.",
    )

    assert result.decision == ReviewDecision.APPROVED


def test_result_rejects_empty_transaction_id():
    with pytest.raises(ValueError):
        ReviewDecisionResult(
            transaction_id="",
            review_id="REVIEW-TX-001",
            decision=ReviewDecision.APPROVED,
            decided_at=datetime.now(timezone.utc),
            decided_by="reviewer",
            reason="Approved.",
        )


def test_result_rejects_empty_review_id():
    with pytest.raises(ValueError):
        ReviewDecisionResult(
            transaction_id="TX-001",
            review_id="",
            decision=ReviewDecision.APPROVED,
            decided_at=datetime.now(timezone.utc),
            decided_by="reviewer",
            reason="Approved.",
        )


def test_result_rejects_empty_reason():
    with pytest.raises(ValueError):
        ReviewDecisionResult(
            transaction_id="TX-001",
            review_id="REVIEW-TX-001",
            decision=ReviewDecision.APPROVED,
            decided_at=datetime.now(timezone.utc),
            decided_by="reviewer",
            reason="",
        )


def test_result_rejects_naive_datetime():
    with pytest.raises(ValueError):
        ReviewDecisionResult(
            transaction_id="TX-001",
            review_id="REVIEW-TX-001",
            decision=ReviewDecision.APPROVED,
            decided_at=datetime.now(),
            decided_by="reviewer",
            reason="Approved.",
        )


def test_result_rejects_invalid_metadata():
    with pytest.raises(TypeError):
        ReviewDecisionResult(
            transaction_id="TX-001",
            review_id="REVIEW-TX-001",
            decision=ReviewDecision.APPROVED,
            decided_at=datetime.now(timezone.utc),
            decided_by="reviewer",
            reason="Approved.",
            metadata=[],
        )


def test_reject_can_include_detailed_reason():
    handler = ReviewDecisionHandler()

    result = handler.reject(
        make_item(),
        decided_by="reviewer-3",
        reason=(
            "Rejected because the debit account does not "
            "match the supporting transaction evidence."
        ),
        metadata={
            "requires_retraining": True,
        },
    )

    assert result.decision == ReviewDecision.REJECTED
    assert result.metadata["requires_retraining"] is True


def test_is_ready():
    handler = ReviewDecisionHandler()

    assert handler.is_ready() is True
