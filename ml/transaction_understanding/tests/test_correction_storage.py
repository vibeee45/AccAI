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
from ml.transaction_understanding.review_decision.schemas import (
    ReviewDecision,
    ReviewDecisionResult,
)
from ml.transaction_understanding.review_queue.schemas import (
    ReviewQueueItem,
    ReviewStatus,
)
from ml.transaction_understanding.transaction_editing.editor import (
    TransactionEditor,
)
from ml.transaction_understanding.correction_storage.config import (
    CorrectionStorageConfig,
)
from ml.transaction_understanding.correction_storage.inference import (
    CorrectionStorageService,
)
from ml.transaction_understanding.correction_storage.schemas import (
    CorrectionRecord,
    CorrectionStatus,
)
from ml.transaction_understanding.correction_storage.storage import (
    CorrectionStore,
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


def make_edit_result():
    editor = TransactionEditor()

    return editor.edit(
        make_prediction(),
        {
            "amount": 6000.0,
            "payment_mode": "UPI",
        },
        edited_by="reviewer-1",
        reason="Corrected amount and payment mode.",
    )


def make_approval():
    return ReviewDecisionResult(
        transaction_id="TX-001",
        review_id="REVIEW-TX-001",
        decision=ReviewDecision.APPROVED,
        decided_at=datetime(
            2026,
            9,
            4,
            21,
            0,
            tzinfo=timezone.utc,
        ),
        decided_by="reviewer-1",
        reason="Reviewed and approved.",
    )


def make_rejection():
    return ReviewDecisionResult(
        transaction_id="TX-001",
        review_id="REVIEW-TX-001",
        decision=ReviewDecision.REJECTED,
        decided_at=datetime(
            2026,
            9,
            4,
            21,
            0,
            tzinfo=timezone.utc,
        ),
        decided_by="reviewer-1",
        reason="Rejected due to incorrect evidence.",
    )


def test_config_defaults():
    config = CorrectionStorageConfig()

    assert config.max_reason_length == 500
    assert config.max_metadata_entries == 100
    assert config.max_records == 100000


def test_config_rejects_invalid_reason_limit():
    with pytest.raises(ValueError):
        CorrectionStorageConfig(
            max_reason_length=0,
        )


def test_config_rejects_invalid_metadata_limit():
    with pytest.raises(ValueError):
        CorrectionStorageConfig(
            max_metadata_entries=0,
        )


def test_config_rejects_invalid_record_limit():
    with pytest.raises(ValueError):
        CorrectionStorageConfig(
            max_records=0,
        )


def test_store_approved_correction():
    store = CorrectionStore()

    edit_result = make_edit_result()
    decision = make_approval()

    record = store.store(
        edit_result,
        decision,
    )

    assert isinstance(
        record,
        CorrectionRecord,
    )

    assert record.correction_id == "CORRECTION-REVIEW-TX-001"
    assert record.transaction_id == "TX-001"
    assert record.review_id == "REVIEW-TX-001"
    assert record.status == CorrectionStatus.APPROVED


def test_store_rejected_correction():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_rejection(),
    )

    assert record.status == CorrectionStatus.REJECTED


def test_store_preserves_original_values():
    store = CorrectionStore()

    edit_result = make_edit_result()

    record = store.store(
        edit_result,
        make_approval(),
    )

    assert record.original_transaction.amount == 5000.0
    assert record.corrected_transaction.amount == 6000.0

    assert record.original_transaction.payment_mode == "NEFT"
    assert record.corrected_transaction.payment_mode == "UPI"


def test_store_preserves_changed_fields():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    assert set(record.changed_fields) == {
        "amount",
        "payment_mode",
    }

    assert record.has_changes is True


def test_store_preserves_reviewer():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    assert record.reviewer == "reviewer-1"


def test_store_preserves_decision_reason():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    assert record.decision_reason == "Reviewed and approved."


def test_store_with_metadata():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
        metadata={
            "source": "review_ui",
            "feedback_candidate": True,
        },
    )

    assert record.metadata["source"] == "review_ui"
    assert record.metadata["feedback_candidate"] is True


def test_store_with_custom_timestamp():
    store = CorrectionStore()

    timestamp = datetime(
        2026,
        9,
        4,
        22,
        0,
        tzinfo=timezone.utc,
    )

    record = store.store(
        make_edit_result(),
        make_approval(),
        created_at=timestamp,
    )

    assert record.created_at == timestamp


def test_store_rejects_naive_timestamp():
    store = CorrectionStore()

    with pytest.raises(ValueError):
        store.store(
            make_edit_result(),
            make_approval(),
            created_at=datetime(
                2026,
                9,
                4,
            ),
        )


def test_store_rejects_mismatched_transaction():
    store = CorrectionStore()

    decision = ReviewDecisionResult(
        transaction_id="TX-999",
        review_id="REVIEW-TX-001",
        decision=ReviewDecision.APPROVED,
        decided_at=datetime.now(timezone.utc),
        decided_by="reviewer",
        reason="Approved.",
    )

    with pytest.raises(ValueError):
        store.store(
            make_edit_result(),
            decision,
        )


def test_store_rejects_duplicate_review():
    store = CorrectionStore()

    store.store(
        make_edit_result(),
        make_approval(),
    )

    with pytest.raises(ValueError):
        store.store(
            make_edit_result(),
            make_approval(),
        )


def test_get_by_correction_id():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    found = store.get(
        record.correction_id,
    )

    assert found is record


def test_get_unknown_correction():
    store = CorrectionStore()

    with pytest.raises(KeyError):
        store.get(
            "CORRECTION-UNKNOWN",
        )


def test_get_by_transaction():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    found = store.get_by_transaction(
        "TX-001",
    )

    assert found is record


def test_get_by_review():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    found = store.get_by_review(
        "REVIEW-TX-001",
    )

    assert found is record


def test_get_by_unknown_transaction():
    store = CorrectionStore()

    with pytest.raises(KeyError):
        store.get_by_transaction(
            "TX-999",
        )


def test_get_by_unknown_review():
    store = CorrectionStore()

    with pytest.raises(KeyError):
        store.get_by_review(
            "REVIEW-999",
        )


def test_list_all():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    records = store.list_all()

    assert records == (record,)


def test_list_approved():
    store = CorrectionStore()

    approved = store.store(
        make_edit_result(),
        make_approval(),
    )

    assert store.list_approved() == (approved,)
    assert store.list_rejected() == ()


def test_list_rejected():
    store = CorrectionStore()

    rejected = store.store(
        make_edit_result(),
        make_rejection(),
    )

    assert store.list_rejected() == (rejected,)
    assert store.list_approved() == ()


def test_contains():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    assert store.contains(
        record.correction_id,
    ) is True

    assert store.contains(
        "UNKNOWN",
    ) is False


def test_remove():
    store = CorrectionStore()

    record = store.store(
        make_edit_result(),
        make_approval(),
    )

    removed = store.remove(
        record.correction_id,
    )

    assert removed is record
    assert len(store) == 0


def test_remove_unknown():
    store = CorrectionStore()

    with pytest.raises(KeyError):
        store.remove(
            "UNKNOWN",
        )


def test_clear():
    store = CorrectionStore()

    store.store(
        make_edit_result(),
        make_approval(),
    )

    assert len(store) == 1

    store.clear()

    assert len(store) == 0


def test_store_many():
    store = CorrectionStore(
        CorrectionStorageConfig(
            max_records=10,
        )
    )

    first_edit = make_edit_result()

    first_decision = make_approval()

    second_prediction = make_prediction()

    second_prediction = TransactionPrediction(
        transaction_id="TX-002",
        raw_text=second_prediction.raw_text,
        normalized_text=second_prediction.normalized_text,
        amount=second_prediction.amount,
        transaction_class=second_prediction.transaction_class,
        classification_confidence=second_prediction.classification_confidence,
        debit_account=second_prediction.debit_account,
        credit_account=second_prediction.credit_account,
        debit_prediction=second_prediction.debit_prediction,
        credit_prediction=second_prediction.credit_prediction,
        payment_mode=second_prediction.payment_mode,
        status=second_prediction.status,
    )

    second_edit = TransactionEditor().edit(
        second_prediction,
        {
            "amount": 7000.0,
        },
        reason="Corrected amount.",
    )

    second_decision = ReviewDecisionResult(
        transaction_id="TX-002",
        review_id="REVIEW-TX-002",
        decision=ReviewDecision.APPROVED,
        decided_at=datetime.now(timezone.utc),
        decided_by="reviewer",
        reason="Approved.",
    )

    records = store.store_many(
        (
            (first_edit, first_decision),
            (second_edit, second_decision),
        )
    )

    assert len(records) == 2
    assert len(store) == 2


def test_max_records():
    store = CorrectionStore(
        CorrectionStorageConfig(
            max_records=1,
        )
    )

    store.store(
        make_edit_result(),
        make_approval(),
    )

    second_prediction = make_prediction()

    second_prediction = TransactionPrediction(
        transaction_id="TX-002",
        raw_text=second_prediction.raw_text,
        normalized_text=second_prediction.normalized_text,
        amount=second_prediction.amount,
        transaction_class=second_prediction.transaction_class,
        classification_confidence=second_prediction.classification_confidence,
        debit_account=second_prediction.debit_account,
        credit_account=second_prediction.credit_account,
        debit_prediction=second_prediction.debit_prediction,
        credit_prediction=second_prediction.credit_prediction,
        payment_mode=second_prediction.payment_mode,
        status=second_prediction.status,
    )

    second_edit = TransactionEditor().edit(
        second_prediction,
        {
            "amount": 7000.0,
        },
        reason="Corrected amount.",
    )

    second_decision = ReviewDecisionResult(
        transaction_id="TX-002",
        review_id="REVIEW-TX-002",
        decision=ReviewDecision.APPROVED,
        decided_at=datetime.now(timezone.utc),
        decided_by="reviewer",
        reason="Approved.",
    )

    with pytest.raises(ValueError):
        store.store(
            second_edit,
            second_decision,
        )


def test_store_is_ready():
    store = CorrectionStore()

    assert store.is_ready() is True


def test_service_store():
    service = CorrectionStorageService()

    result = service.store(
        make_edit_result(),
        make_approval(),
        metadata={
            "source": "test",
        },
    )

    assert isinstance(
        result,
        CorrectionRecord,
    )

    assert result.status == CorrectionStatus.APPROVED


def test_service_get():
    service = CorrectionStorageService()

    record = service.store(
        make_edit_result(),
        make_approval(),
    )

    assert service.get(
        record.correction_id,
    ) is record


def test_service_get_by_transaction():
    service = CorrectionStorageService()

    record = service.store(
        make_edit_result(),
        make_approval(),
    )

    assert service.get_by_transaction(
        "TX-001",
    ) is record


def test_service_get_by_review():
    service = CorrectionStorageService()

    record = service.store(
        make_edit_result(),
        make_approval(),
    )

    assert service.get_by_review(
        "REVIEW-TX-001",
    ) is record


def test_service_lists():
    service = CorrectionStorageService()

    approved = service.store(
        make_edit_result(),
        make_approval(),
    )

    assert service.list_all() == (approved,)
    assert service.list_approved() == (approved,)


def test_service_remove():
    service = CorrectionStorageService()

    record = service.store(
        make_edit_result(),
        make_approval(),
    )

    removed = service.remove(
        record.correction_id,
    )

    assert removed is record
    assert len(service) == 0


def test_service_contains():
    service = CorrectionStorageService()

    record = service.store(
        make_edit_result(),
        make_approval(),
    )

    assert service.contains(
        record.correction_id,
    )


def test_service_clear():
    service = CorrectionStorageService()

    service.store(
        make_edit_result(),
        make_approval(),
    )

    service.clear()

    assert len(service) == 0


def test_service_is_ready():
    service = CorrectionStorageService()

    assert service.is_ready() is True
