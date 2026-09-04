from datetime import datetime, timezone
from enum import Enum

import pytest

from ml.transaction_understanding.correction_storage.schemas import (
    CorrectionRecord,
    CorrectionStatus,
)
from ml.transaction_understanding.feedback_dataset import (
    FeedbackDataset,
    FeedbackDatasetBuilder,
    FeedbackDatasetConfig,
    FeedbackDatasetRepository,
    FeedbackDatasetService,
    FeedbackExample,
    FeedbackLabel,
)
from ml.transaction_understanding.prediction.schemas import (
    PredictionAccount,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionStatus,
    TransactionPrediction,
)
from ml.transaction_understanding.confidence_routing.schemas import (
    RoutingDecision,
    RoutingResult,
)
from ml.transaction_understanding.review_queue.schemas import (
    ReviewQueueItem,
    ReviewStatus,
)
from ml.transaction_understanding.review_decision.decision import (
    ReviewDecisionHandler,
)
from ml.transaction_understanding.review_decision.schemas import (
    ReviewDecision,
)
from ml.transaction_understanding.transaction_editing.editor import (
    TransactionEditor,
)
from ml.transaction_understanding.transaction_editing.schemas import (
    TransactionEdit,
    TransactionEditResult,
    utc_now as editing_utc_now,
)


def make_prediction(transaction_id: str = "txn-001"):
    debit_account = PredictionAccount(
        account_id="rent_expense",
        account_name="Rent Expense",
        confidence=0.91,
    )

    credit_account = PredictionAccount(
        account_id="bank",
        account_name="Bank",
        confidence=0.94,
    )

    debit_prediction = PredictionDirection(
        account_id="rent_expense",
        account_name="Rent Expense",
        direction="debit",
        confidence=0.91,
        reason="Rent is an expense and is debited.",
        requires_review=False,
    )

    credit_prediction = PredictionDirection(
        account_id="bank",
        account_name="Bank",
        direction="credit",
        confidence=0.94,
        reason="Bank is credited when money is paid from the bank.",
        requires_review=False,
    )

    payment_mode = PredictionPaymentMode(
        mode="UPI",
        confidence=0.96,
        requires_review=False,
    )

    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="Paid rent of Rs 25000 by UPI",
        normalized_text="paid rent of rs 25000 by upi",
        amount=25000.0,
        transaction_class="rent",
        classification_confidence=0.91,
        debit_account=debit_account,
        credit_account=credit_account,
        debit_prediction=debit_prediction,
        credit_prediction=credit_prediction,
        payment_mode=payment_mode,
        status=PredictionStatus.SUCCESS,
    )


def make_correction(
    status=CorrectionStatus.APPROVED,
    changed=True,
    transaction_id="txn-001",
    review_id="review-001",
    correction_id="corr-001",
):
    prediction = make_prediction(transaction_id)

    routing = RoutingResult(
        decision=RoutingDecision.HUMAN_REVIEW,
        confidence=0.60,
        reason="Low confidence prediction requires human review.",
        requires_review=True,
        retryable=False,
    )

    review_item = ReviewQueueItem(
        review_id=review_id,
        transaction_id=transaction_id,
        prediction=prediction,
        routing=routing,
        status=ReviewStatus.PENDING,
        priority=1,
        reason="Low confidence prediction.",
        created_at=editing_utc_now(),
    )

    editor = TransactionEditor()

    if changed:
        edit_result = editor.edit(
            prediction,
            changes={
                "transaction_class": "salary",
            },
            edited_by="reviewer-1",
            reason="Human correction",
        )
    else:
        original = editor.snapshot(prediction)

        edit_result = TransactionEditResult(
            original=original,
            edited=original,
            edits=(),
            edited_at=editing_utc_now(),
            edited_by="reviewer-1",
            reason="No changes required",
            metadata={},
        )

    decision_handler = ReviewDecisionHandler()

    if status == CorrectionStatus.APPROVED:
        decision_result = decision_handler.approve(
            review_item,
            decided_by="reviewer-1",
            reason="Human correction approved",
        )
    else:
        decision_result = decision_handler.reject(
            review_item,
            decided_by="reviewer-1",
            reason="Human correction rejected",
        )

    return CorrectionRecord(
        correction_id=correction_id,
        transaction_id=transaction_id,
        review_id=review_id,
        edit_result=edit_result,
        decision_result=decision_result,
        status=status,
        created_at=editing_utc_now(),
        metadata={"source": "test"},
    )

def test_feedback_label_values():
    assert FeedbackLabel.APPROVED.value == "approved"
    assert FeedbackLabel.REJECTED.value == "rejected"


def test_builder_creates_approved_example():
    correction = make_correction()

    builder = FeedbackDatasetBuilder()

    example = builder.build_example(correction)

    assert isinstance(example, FeedbackExample)
    assert example.transaction_id == "txn-001"
    assert example.review_id == "review-001"
    assert example.label == FeedbackLabel.APPROVED
    assert example.is_approved is True
    assert example.is_rejected is False


def test_builder_preserves_original_and_corrected_values():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.original_transaction_class == "rent"
    assert example.corrected_transaction_class == "salary"


def test_builder_preserves_original_text():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.original_text == (
        "Paid rent of Rs 25000 by UPI"
    )


def test_builder_preserves_corrected_text():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.corrected_text == (
        "Paid rent of Rs 25000 by UPI"
    )


def test_builder_preserves_changed_fields():
    correction = make_correction(changed=True)

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert "transaction_class" in example.changed_fields
    assert example.has_changes is True


def test_builder_handles_no_changes():
    correction = make_correction(changed=False)

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.has_changes is False
    assert example.changed_fields == ()


def test_training_dict_uses_corrected_values():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    record = example.to_training_dict()

    assert record["text"] == example.corrected_text
    assert (
        record["transaction_class"]
        == example.corrected_transaction_class
    )
    assert (
        record["debit_account_id"]
        == example.corrected_debit_account_id
    )
    assert (
        record["credit_account_id"]
        == example.corrected_credit_account_id
    )
    assert (
        record["payment_mode"]
        == example.corrected_payment_mode
    )


def test_training_dict_contains_changed_fields():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    record = example.to_training_dict()

    assert isinstance(
        record["changed_fields"],
        list,
    )
    assert "transaction_class" in (
        record["changed_fields"]
    )


def test_builder_excludes_rejected_by_default():
    correction = make_correction(
        status=CorrectionStatus.REJECTED
    )

    config = FeedbackDatasetConfig(
        include_rejected=False
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction]
    )

    assert dataset.count == 0


def test_builder_can_include_rejected():
    correction = make_correction(
        status=CorrectionStatus.REJECTED
    )

    config = FeedbackDatasetConfig(
        include_rejected=True
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction]
    )

    assert dataset.count == 1
    assert dataset.rejected_count == 1
    assert dataset.approved_count == 0


def test_rejected_example_has_rejected_label():
    correction = make_correction(
        status=CorrectionStatus.REJECTED
    )

    config = FeedbackDatasetConfig(
        include_rejected=True
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction]
    )

    assert (
        dataset.examples[0].label
        == FeedbackLabel.REJECTED
    )

    assert dataset.examples[0].is_rejected is True


def test_require_changes_filters_unchanged_records():
    correction = make_correction(
        changed=False
    )

    config = FeedbackDatasetConfig(
        require_changes=True
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction]
    )

    assert dataset.count == 0


def test_require_changes_keeps_changed_records():
    correction = make_correction(
        changed=True
    )

    config = FeedbackDatasetConfig(
        require_changes=True
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction]
    )

    assert dataset.count == 1


def test_builder_deduplicates_records():
    correction = make_correction()

    config = FeedbackDatasetConfig(
        deduplicate=True
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction, correction]
    )

    assert dataset.count == 1


def test_builder_can_disable_deduplication():
    correction_1 = make_correction(
        transaction_id="txn-001",
        review_id="review-001",
        correction_id="corr-001",
    )

    correction_2 = make_correction(
        transaction_id="txn-001",
        review_id="review-002",
        correction_id="corr-002",
    )

    config = FeedbackDatasetConfig(
        deduplicate=False
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction_1, correction_2]
    )

    assert dataset.count == 2


def test_max_examples():
    correction_1 = make_correction(
        transaction_id="txn-001",
        review_id="review-001",
        correction_id="corr-001",
    )

    correction_2 = make_correction(
        transaction_id="txn-002",
        review_id="review-002",
        correction_id="corr-002",
    )

    config = FeedbackDatasetConfig(
        max_examples=1
    )

    dataset = FeedbackDatasetBuilder(config).build(
        [correction_1, correction_2]
    )

    assert dataset.count == 1


def test_config_defaults():
    config = FeedbackDatasetConfig()

    assert config.include_approved is True
    assert config.include_rejected is False
    assert config.require_changes is False
    assert config.deduplicate is True
    assert config.max_examples is None


def test_config_rejects_invalid_max_examples():
    with pytest.raises(ValueError):
        FeedbackDatasetConfig(max_examples=0)


def test_config_rejects_non_boolean_include_approved():
    with pytest.raises(TypeError):
        FeedbackDatasetConfig(
            include_approved="yes"
        )


def test_config_rejects_non_boolean_deduplicate():
    with pytest.raises(TypeError):
        FeedbackDatasetConfig(
            deduplicate="yes"
        )


def test_repository_add_and_get():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    assert repository.get(
        example.feedback_id
    ) == example

    assert len(repository) == 1


def test_repository_duplicate_rejected():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    with pytest.raises(ValueError):
        repository.add(example)


def test_repository_get_by_transaction():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    results = repository.get_by_transaction(
        "txn-001"
    )

    assert len(results) == 1
    assert results[0] == example


def test_repository_lists_approved():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    assert repository.list_approved() == [example]
    assert repository.list_rejected() == []


def test_repository_lists_rejected():
    correction = make_correction(
        status=CorrectionStatus.REJECTED
    )

    config = FeedbackDatasetConfig(
        include_rejected=True
    )

    example = FeedbackDatasetBuilder(config).build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    assert repository.list_rejected() == [example]
    assert repository.list_approved() == []


def test_repository_remove():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    removed = repository.remove(
        example.feedback_id
    )

    assert removed == example
    assert len(repository) == 0


def test_repository_remove_missing_returns_none():
    repository = FeedbackDatasetRepository()

    assert repository.remove("missing") is None


def test_repository_contains():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    assert repository.contains(
        example.feedback_id
    )

    assert not repository.contains("missing")


def test_repository_clear():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    repository.clear()

    assert len(repository) == 0


def test_repository_add_many():
    correction_1 = make_correction(
        transaction_id="txn-001",
        review_id="review-001",
        correction_id="corr-001",
    )

    correction_2 = make_correction(
        transaction_id="txn-002",
        review_id="review-002",
        correction_id="corr-002",
    )

    builder = FeedbackDatasetBuilder()

    examples = (
        builder.build_example(correction_1),
        builder.build_example(correction_2),
    )

    repository = FeedbackDatasetRepository()

    added = repository.add_many(examples)

    assert added == 2
    assert len(repository) == 2


def test_repository_build_dataset():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    repository = FeedbackDatasetRepository()

    repository.add(example)

    dataset = repository.build_dataset(
        metadata={"test": True}
    )

    assert isinstance(dataset, FeedbackDataset)
    assert dataset.count == 1
    assert dataset.metadata["test"] is True


def test_dataset_counts():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    dataset = FeedbackDataset(
        examples=(example,)
    )

    assert dataset.count == 1
    assert dataset.approved_count == 1
    assert dataset.rejected_count == 0
    assert dataset.corrected_count == 1


def test_dataset_training_records():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    dataset = FeedbackDataset(
        examples=(example,)
    )

    records = dataset.to_training_records()

    assert len(records) == 1
    assert records[0]["transaction_id"] == "txn-001"


def test_service_build():
    correction = make_correction()

    service = FeedbackDatasetService()

    dataset = service.build(
        [correction]
    )

    assert dataset.count == 1
    assert len(service) == 1


def test_service_add_correction():
    correction = make_correction()

    service = FeedbackDatasetService()

    example = service.add_correction(
        correction
    )

    assert example is not None
    assert len(service) == 1


def test_service_ignores_rejected_by_default():
    correction = make_correction(
        status=CorrectionStatus.REJECTED
    )

    service = FeedbackDatasetService()

    example = service.add_correction(
        correction
    )

    assert example is None
    assert len(service) == 0


def test_service_can_include_rejected():
    correction = make_correction(
        status=CorrectionStatus.REJECTED
    )

    service = FeedbackDatasetService(
        FeedbackDatasetConfig(
            include_rejected=True
        )
    )

    example = service.add_correction(
        correction
    )

    assert example is not None
    assert example.is_rejected is True
    assert len(service) == 1


def test_service_deduplicates_same_correction():
    correction = make_correction()

    service = FeedbackDatasetService()

    first = service.add_correction(correction)
    second = service.add_correction(correction)

    assert first == second
    assert len(service) == 1


def test_service_clear():
    correction = make_correction()

    service = FeedbackDatasetService()

    service.add_correction(correction)

    service.clear()

    assert len(service) == 0


def test_service_dataset():
    correction = make_correction()

    service = FeedbackDatasetService()

    service.add_correction(correction)

    dataset = service.dataset()

    assert isinstance(dataset, FeedbackDataset)
    assert dataset.count == 1


def test_service_get_by_transaction():
    correction = make_correction()

    service = FeedbackDatasetService()

    service.add_correction(correction)

    results = service.get_by_transaction(
        "txn-001"
    )

    assert len(results) == 1
    assert results[0].transaction_id == "txn-001"


def test_service_get():
    correction = make_correction()

    service = FeedbackDatasetService()

    example = service.add_correction(
        correction
    )

    assert example is not None

    result = service.get(
        example.feedback_id
    )

    assert result == example


def test_builder_rejects_invalid_correction():
    builder = FeedbackDatasetBuilder()

    with pytest.raises(TypeError):
        builder.build_example("invalid")


def test_builder_rejects_invalid_collection_item():
    builder = FeedbackDatasetBuilder()

    with pytest.raises(TypeError):
        builder.build(["invalid"])


def test_feedback_example_has_changes_property():
    correction = make_correction(
        changed=True
    )

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.has_changes is True


def test_feedback_example_approval_properties():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.is_approved
    assert not example.is_rejected


def test_feedback_example_preserves_metadata():
    correction = make_correction()

    example = FeedbackDatasetBuilder().build_example(
        correction
    )

    assert example.metadata["source"] == "test"
    assert (
        example.metadata["correction_id"]
        == "corr-001"
    )
    assert (
        example.metadata["decision"]
        == "approved"
    )




