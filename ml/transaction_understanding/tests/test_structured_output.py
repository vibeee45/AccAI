import json

import pytest

from ml.transaction_understanding.prediction import (
    PredictionAccount,
    PredictionConfidence,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionSemanticMatch,
    PredictionStatus,
    TransactionPrediction,
)

from ml.transaction_understanding.structured_output import (
    StructuredAccount,
    StructuredBatch,
    StructuredConfidence,
    StructuredDirection,
    StructuredOutputConfig,
    StructuredOutputSerializer,
    StructuredOutputService,
    StructuredPaymentMode,
    StructuredSemanticMatch,
    StructuredTransaction,
)


def make_prediction(
    transaction_id="txn-001",
):
    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="received cash from customer",
        normalized_text=(
            "received cash from customer"
        ),
        amount=1000.0,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=PredictionAccount(
            account_id="cash",
            account_name="Cash",
            confidence=0.96,
        ),
        credit_account=PredictionAccount(
            account_id="sales",
            account_name="Sales",
            confidence=0.94,
        ),
        debit_prediction=PredictionDirection(
            account_id="cash",
            account_name="Cash",
            direction="debit",
            confidence=0.98,
            reason="Cash is the debit account.",
            requires_review=False,
        ),
        credit_prediction=PredictionDirection(
            account_id="sales",
            account_name="Sales",
            direction="credit",
            confidence=0.97,
            reason="Sales is the credit account.",
            requires_review=False,
        ),
        payment_mode=PredictionPaymentMode(
            mode="cash",
            confidence=0.99,
            requires_review=False,
        ),
        confidence=PredictionConfidence(
            overall=0.96,
            requires_review=False,
            reason="High confidence prediction.",
        ),
        semantic_matches=(
            PredictionSemanticMatch(
                candidate_id="sales-001",
                candidate_text="cash sale",
                similarity=0.91,
            ),
        ),
        entities=("customer",),
        metadata={
            "source": "excel",
            "row_number": 5,
        },
        status=PredictionStatus.SUCCESS,
    )


def test_config_defaults():
    config = StructuredOutputConfig()

    assert config.include_entities is True
    assert config.include_semantic_matches is True
    assert config.include_metadata is True
    assert config.include_reasons is True


def test_config_can_disable_optional_fields():
    config = StructuredOutputConfig(
        include_entities=False,
        include_semantic_matches=False,
        include_metadata=False,
        include_reasons=False,
    )

    assert config.include_entities is False
    assert config.include_semantic_matches is False
    assert config.include_metadata is False
    assert config.include_reasons is False


def test_config_rejects_invalid_entities_flag():
    with pytest.raises(TypeError):
        StructuredOutputConfig(
            include_entities="yes"
        )


def test_structured_account():
    account = StructuredAccount(
        account_id="cash",
        account_name="Cash",
        confidence=0.95,
    )

    assert account.account_id == "cash"
    assert account.account_name == "Cash"


def test_structured_direction():
    direction = StructuredDirection(
        account_id="cash",
        direction="debit",
        confidence=0.95,
    )

    assert direction.direction == "debit"
    assert direction.reason is None


def test_structured_payment_mode():
    payment = StructuredPaymentMode(
        mode="upi",
        confidence=0.94,
        requires_review=False,
    )

    assert payment.mode == "upi"


def test_structured_semantic_match():
    match = StructuredSemanticMatch(
        candidate_id="candidate-1",
        candidate_text="cash sale",
        similarity=0.90,
    )

    assert match.similarity == 0.90


def test_structured_confidence():
    confidence = StructuredConfidence(
        overall=0.91,
        requires_review=False,
        reason="High confidence.",
    )

    assert confidence.overall == 0.91


def test_structured_transaction():
    transaction = StructuredTransaction(
        transaction_id="txn-001",
        raw_text="cash sale",
        normalized_text="cash sale",
        amount=1000,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=StructuredAccount(
            "cash",
            "Cash",
            0.95,
        ),
        credit_account=StructuredAccount(
            "sales",
            "Sales",
            0.95,
        ),
        debit=StructuredDirection(
            "cash",
            "debit",
            0.95,
        ),
        credit=StructuredDirection(
            "sales",
            "credit",
            0.95,
        ),
        payment_mode=StructuredPaymentMode(
            "cash",
            0.98,
            False,
        ),
    )

    assert transaction.transaction_id == "txn-001"


def test_serializer_returns_structured_transaction():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert isinstance(
        result,
        StructuredTransaction,
    )

    assert result.transaction_id == "txn-001"
    assert result.amount == 1000.0


def test_serializer_preserves_accounts():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert result.debit_account.account_id == "cash"
    assert result.credit_account.account_id == "sales"


def test_serializer_preserves_directions():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert result.debit.direction == "debit"
    assert result.credit.direction == "credit"


def test_serializer_preserves_payment_mode():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert result.payment_mode.mode == "cash"


def test_serializer_preserves_confidence():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert result.confidence is not None
    assert result.confidence.overall == 0.96


def test_serializer_preserves_entities():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert result.entities == ("customer",)


def test_serializer_preserves_semantic_matches():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert len(
        result.semantic_matches
    ) == 1

    assert (
        result.semantic_matches[0].candidate_id
        == "sales-001"
    )


def test_serializer_preserves_metadata():
    serializer = StructuredOutputSerializer()

    result = serializer.serialize(
        make_prediction()
    )

    assert result.metadata["source"] == "excel"
    assert result.metadata["row_number"] == 5


def test_to_dict():
    serializer = StructuredOutputSerializer()

    result = serializer.to_dict(
        make_prediction()
    )

    assert isinstance(result, dict)
    assert result["transaction_id"] == "txn-001"
    assert result["amount"] == 1000.0
    assert (
        result["transaction_class"]
        == "sales"
    )


def test_to_dict_contains_nested_accounts():
    serializer = StructuredOutputSerializer()

    result = serializer.to_dict(
        make_prediction()
    )

    assert (
        result["debit_account"]["account_id"]
        == "cash"
    )

    assert (
        result["credit_account"]["account_id"]
        == "sales"
    )


def test_to_dict_contains_payment_mode():
    serializer = StructuredOutputSerializer()

    result = serializer.to_dict(
        make_prediction()
    )

    assert (
        result["payment_mode"]["mode"]
        == "cash"
    )


def test_to_dict_contains_status():
    serializer = StructuredOutputSerializer()

    result = serializer.to_dict(
        make_prediction()
    )

    assert result["status"] == "success"


def test_to_dict_contains_semantic_matches():
    serializer = StructuredOutputSerializer()

    result = serializer.to_dict(
        make_prediction()
    )

    assert len(
        result["semantic_matches"]
    ) == 1


def test_to_json_returns_valid_json():
    serializer = StructuredOutputSerializer()

    result = serializer.to_json(
        make_prediction()
    )

    parsed = json.loads(result)

    assert parsed["transaction_id"] == "txn-001"
    assert parsed["amount"] == 1000.0


def test_to_json_is_deterministic():
    serializer = StructuredOutputSerializer()

    first = serializer.to_json(
        make_prediction()
    )

    second = serializer.to_json(
        make_prediction()
    )

    assert first == second


def test_optional_fields_can_be_removed():
    serializer = StructuredOutputSerializer(
        StructuredOutputConfig(
            include_entities=False,
            include_semantic_matches=False,
            include_metadata=False,
            include_reasons=False,
        )
    )

    result = serializer.serialize(
        make_prediction()
    )

    assert result.entities == ()
    assert result.semantic_matches == ()
    assert result.metadata == {}
    assert result.debit.reason is None
    assert result.credit.reason is None


def test_service_serialize():
    service = StructuredOutputService()

    result = service.serialize(
        make_prediction()
    )

    assert isinstance(
        result,
        StructuredTransaction,
    )


def test_service_to_dict():
    service = StructuredOutputService()

    result = service.to_dict(
        make_prediction()
    )

    assert result["transaction_id"] == "txn-001"


def test_service_to_json():
    service = StructuredOutputService()

    result = service.to_json(
        make_prediction()
    )

    parsed = json.loads(result)

    assert parsed["transaction_id"] == "txn-001"


def test_service_ready():
    service = StructuredOutputService()

    assert service.is_ready() is True


def test_serializer_rejects_invalid_prediction():
    serializer = StructuredOutputSerializer()

    with pytest.raises(TypeError):
        serializer.serialize(
            "not a prediction"
        )


def test_structured_batch():
    first = StructuredTransaction(
        transaction_id="txn-001",
        raw_text="cash sale",
        normalized_text="cash sale",
        amount=1000,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=StructuredAccount(
            "cash",
            "Cash",
            0.95,
        ),
        credit_account=StructuredAccount(
            "sales",
            "Sales",
            0.95,
        ),
        debit=StructuredDirection(
            "cash",
            "debit",
            0.95,
        ),
        credit=StructuredDirection(
            "sales",
            "credit",
            0.95,
        ),
        payment_mode=StructuredPaymentMode(
            "cash",
            0.98,
            False,
        ),
    )

    second = StructuredTransaction(
        transaction_id="txn-002",
        raw_text="paid rent",
        normalized_text="paid rent",
        amount=5000,
        transaction_class="rent",
        classification_confidence=0.92,
        debit_account=StructuredAccount(
            "rent_expense",
            "Rent Expense",
            0.94,
        ),
        credit_account=StructuredAccount(
            "bank",
            "Bank",
            0.93,
        ),
        debit=StructuredDirection(
            "rent_expense",
            "debit",
            0.94,
        ),
        credit=StructuredDirection(
            "bank",
            "credit",
            0.93,
        ),
        payment_mode=StructuredPaymentMode(
            "bank_transfer",
            0.97,
            False,
        ),
    )

    batch = StructuredBatch(
        transactions=(first, second)
    )

    assert batch.count == 2


def test_structured_batch_rejects_duplicate_ids():
    transaction = StructuredTransaction(
        transaction_id="txn-001",
        raw_text="cash sale",
        normalized_text="cash sale",
        amount=1000,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=StructuredAccount(
            "cash",
            "Cash",
            0.95,
        ),
        credit_account=StructuredAccount(
            "sales",
            "Sales",
            0.95,
        ),
        debit=StructuredDirection(
            "cash",
            "debit",
            0.95,
        ),
        credit=StructuredDirection(
            "sales",
            "credit",
            0.95,
        ),
        payment_mode=StructuredPaymentMode(
            "cash",
            0.98,
            False,
        ),
    )

    with pytest.raises(ValueError):
        StructuredBatch(
            transactions=(
                transaction,
                transaction,
            )
        )


def test_failed_prediction_status_is_preserved():
    prediction = make_prediction()

    failed = TransactionPrediction(
        transaction_id="txn-failed",
        raw_text=prediction.raw_text,
        normalized_text=prediction.normalized_text,
        amount=prediction.amount,
        transaction_class=prediction.transaction_class,
        classification_confidence=prediction.classification_confidence,
        debit_account=prediction.debit_account,
        credit_account=prediction.credit_account,
        debit_prediction=prediction.debit_prediction,
        credit_prediction=prediction.credit_prediction,
        payment_mode=prediction.payment_mode,
        status=PredictionStatus.FAILED,
    )

    serializer = StructuredOutputSerializer()

    result = serializer.serialize(failed)

    assert result.status == "failed"


def test_review_status_is_preserved():
    prediction = make_prediction()

    review = TransactionPrediction(
        transaction_id="txn-review",
        raw_text=prediction.raw_text,
        normalized_text=prediction.normalized_text,
        amount=prediction.amount,
        transaction_class=prediction.transaction_class,
        classification_confidence=prediction.classification_confidence,
        debit_account=prediction.debit_account,
        credit_account=prediction.credit_account,
        debit_prediction=prediction.debit_prediction,
        credit_prediction=prediction.credit_prediction,
        payment_mode=prediction.payment_mode,
        status=PredictionStatus.REVIEW_REQUIRED,
    )

    serializer = StructuredOutputSerializer()

    result = serializer.serialize(review)

    assert result.status == "review_required"
