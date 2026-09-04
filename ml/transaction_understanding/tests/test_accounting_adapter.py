import pytest

from ml.transaction_understanding.prediction import (
    PredictionAccount,
    PredictionConfidence,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionStatus,
    TransactionPrediction,
)

from ml.transaction_understanding.structured_output import (
    StructuredOutputSerializer,
)

from ml.transaction_understanding.accounting_adapter import (
    AccountingAccount,
    AccountingAdapterConfig,
    AccountingAdapterResult,
    AccountingAdapterService,
    AccountingTransaction,
    AIToAccountingAdapter,
)


def make_prediction(
    amount=1000.0,
    status=PredictionStatus.SUCCESS,
):
    return TransactionPrediction(
        transaction_id="txn-001",
        raw_text="received cash from customer",
        normalized_text="received cash from customer",
        amount=amount,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=PredictionAccount(
            "cash",
            "Cash",
            0.96,
        ),
        credit_account=PredictionAccount(
            "sales",
            "Sales",
            0.94,
        ),
        debit_prediction=PredictionDirection(
            "cash",
            "Cash",
            "debit",
            0.98,
            "Cash is debited.",
            False,
        ),
        credit_prediction=PredictionDirection(
            "sales",
            "Sales",
            "credit",
            0.97,
            "Sales is credited.",
            False,
        ),
        payment_mode=PredictionPaymentMode(
            "cash",
            0.99,
            False,
        ),
        confidence=PredictionConfidence(
            0.96,
            False,
            "High confidence prediction.",
        ),
        metadata={
            "source": "excel",
            "row": 5,
        },
        status=status,
    )


def make_structured(
    amount=1000.0,
    status=PredictionStatus.SUCCESS,
):
    serializer = StructuredOutputSerializer()

    return serializer.serialize(
        make_prediction(
            amount=amount,
            status=status,
        )
    )


def test_config_defaults():
    config = AccountingAdapterConfig()

    assert config.require_amount is True
    assert config.require_valid_accounts is True
    assert config.require_valid_directions is True
    assert config.require_confidence is True
    assert config.minimum_confidence == 0.80


def test_config_custom_threshold():
    config = AccountingAdapterConfig(
        minimum_confidence=0.90
    )

    assert config.minimum_confidence == 0.90


def test_config_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        AccountingAdapterConfig(
            minimum_confidence=1.2
        )


def test_accounting_account():
    account = AccountingAccount(
        "cash",
        "Cash",
    )

    assert account.account_id == "cash"
    assert account.account_name == "Cash"


def test_accounting_account_rejects_empty_id():
    with pytest.raises(ValueError):
        AccountingAccount(
            "",
            "Cash",
        )


def test_accounting_transaction():
    transaction = AccountingTransaction(
        transaction_id="txn-001",
        description="cash sale",
        amount=1000,
        debit_account=AccountingAccount(
            "cash",
            "Cash",
        ),
        credit_account=AccountingAccount(
            "sales",
            "Sales",
        ),
        transaction_class="sales",
        payment_mode="cash",
        ai_confidence=0.95,
        requires_review=False,
        source_text="cash sale",
        normalized_text="cash sale",
    )

    assert transaction.amount == 1000
    assert transaction.debit_account.account_id == "cash"


def test_accounting_transaction_rejects_zero_amount():
    with pytest.raises(ValueError):
        AccountingTransaction(
            transaction_id="txn-001",
            description="cash sale",
            amount=0,
            debit_account=AccountingAccount(
                "cash",
                "Cash",
            ),
            credit_account=AccountingAccount(
                "sales",
                "Sales",
            ),
            transaction_class="sales",
            payment_mode="cash",
            ai_confidence=0.95,
            requires_review=False,
            source_text="cash sale",
            normalized_text="cash sale",
        )


def test_adapter_success():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert result.success is True
    assert result.transaction is not None
    assert result.errors == ()


def test_adapter_maps_transaction_id():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.transaction_id
        == "txn-001"
    )


def test_adapter_maps_amount():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured(2500)
    )

    assert result.transaction.amount == 2500


def test_adapter_maps_debit_account():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.debit_account.account_id
        == "cash"
    )

    assert (
        result.transaction.debit_account.account_name
        == "Cash"
    )


def test_adapter_maps_credit_account():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.credit_account.account_id
        == "sales"
    )

    assert (
        result.transaction.credit_account.account_name
        == "Sales"
    )


def test_adapter_maps_transaction_class():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.transaction_class
        == "sales"
    )


def test_adapter_maps_payment_mode():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.payment_mode
        == "cash"
    )


def test_adapter_maps_confidence():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.ai_confidence
        == 0.96
    )


def test_adapter_maps_metadata():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.metadata["source"]
        == "excel"
    )


def test_adapter_preserves_source_text():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.source_text
        == "received cash from customer"
    )


def test_adapter_preserves_normalized_text():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured()
    )

    assert (
        result.transaction.normalized_text
        == "received cash from customer"
    )


def test_adapter_rejects_invalid_input():
    adapter = AIToAccountingAdapter()

    with pytest.raises(TypeError):
        adapter.adapt("invalid")


def test_adapter_rejects_missing_amount():
    structured = make_structured()

    structured = structured.__class__(
        transaction_id=structured.transaction_id,
        raw_text=structured.raw_text,
        normalized_text=structured.normalized_text,
        amount=None,
        transaction_class=structured.transaction_class,
        classification_confidence=structured.classification_confidence,
        debit_account=structured.debit_account,
        credit_account=structured.credit_account,
        debit=structured.debit,
        credit=structured.credit,
        payment_mode=structured.payment_mode,
        confidence=structured.confidence,
        entities=structured.entities,
        semantic_matches=structured.semantic_matches,
        metadata=structured.metadata,
        status=structured.status,
    )

    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        structured
    )

    assert result.success is False
    assert any(
        "amount" in error.lower()
        for error in result.errors
    )


def test_adapter_rejects_failed_prediction():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured(
            status=PredictionStatus.FAILED
        )
    )

    assert result.success is False
    assert any(
        "status" in error.lower()
        for error in result.errors
    )


def test_adapter_rejects_review_prediction():
    adapter = AIToAccountingAdapter()

    result = adapter.adapt(
        make_structured(
            status=PredictionStatus.REVIEW_REQUIRED
        )
    )

    assert result.success is False
    assert any(
        "status" in error.lower()
        for error in result.errors
    )


def test_low_confidence_generates_warning():
    prediction = make_prediction()

    low_confidence = prediction.__class__(
        transaction_id=prediction.transaction_id,
        raw_text=prediction.raw_text,
        normalized_text=prediction.normalized_text,
        amount=prediction.amount,
        transaction_class=prediction.transaction_class,
        classification_confidence=0.60,
        debit_account=prediction.debit_account,
        credit_account=prediction.credit_account,
        debit_prediction=prediction.debit_prediction,
        credit_prediction=prediction.credit_prediction,
        payment_mode=prediction.payment_mode,
        confidence=PredictionConfidence(
            0.60,
            True,
            "Low confidence; human review required.",
        ),
        metadata=prediction.metadata,
        status=PredictionStatus.SUCCESS,
    )

    structured = StructuredOutputSerializer().serialize(
        low_confidence
    )

    result = AIToAccountingAdapter().adapt(
        structured
    )

    assert result.success is True
    assert result.transaction.requires_review is True
    assert len(result.warnings) > 0


def test_custom_confidence_threshold():
    config = AccountingAdapterConfig(
        minimum_confidence=0.95
    )

    adapter = AIToAccountingAdapter(
        config
    )

    prediction = make_prediction()

    prediction = prediction.__class__(
        transaction_id=prediction.transaction_id,
        raw_text=prediction.raw_text,
        normalized_text=prediction.normalized_text,
        amount=prediction.amount,
        transaction_class=prediction.transaction_class,
        classification_confidence=0.90,
        debit_account=prediction.debit_account,
        credit_account=prediction.credit_account,
        debit_prediction=prediction.debit_prediction,
        credit_prediction=prediction.credit_prediction,
        payment_mode=prediction.payment_mode,
        confidence=PredictionConfidence(
            0.90,
            False,
            "Confidence calculated.",
        ),
        metadata=prediction.metadata,
        status=PredictionStatus.SUCCESS,
    )

    structured = StructuredOutputSerializer().serialize(
        prediction
    )

    result = adapter.adapt(
        structured
    )

    assert result.success is True
    assert result.transaction.requires_review is True


def test_adapter_many():
    adapter = AIToAccountingAdapter()

    transactions = (
        make_structured(1000),
        make_structured(2000).__class__(
            transaction_id="txn-002",
            raw_text="received cash from customer",
            normalized_text="received cash from customer",
            amount=2000,
            transaction_class="sales",
            classification_confidence=0.95,
            debit_account=make_structured(2000).debit_account,
            credit_account=make_structured(2000).credit_account,
            debit=make_structured(2000).debit,
            credit=make_structured(2000).credit,
            payment_mode=make_structured(2000).payment_mode,
            confidence=make_structured(2000).confidence,
            entities=(),
            semantic_matches=(),
            metadata={},
            status="success",
        ),
    )

    results = adapter.adapt_many(
        transactions
    )

    assert len(results) == 2
    assert all(
        result.success
        for result in results
    )


def test_service_adapt():
    service = AccountingAdapterService()

    result = service.adapt(
        make_structured()
    )

    assert result.success is True


def test_service_adapt_many():
    service = AccountingAdapterService()

    results = service.adapt_many(
        (
            make_structured(),
        )
    )

    assert len(results) == 1
    assert results[0].success is True


def test_service_ready():
    service = AccountingAdapterService()

    assert service.is_ready() is True


def test_successful_result_requires_transaction():
    with pytest.raises(ValueError):
        AccountingAdapterResult(
            success=True,
            transaction=None,
        )


def test_failed_result_cannot_have_transaction():
    transaction = AccountingTransaction(
        transaction_id="txn",
        description="test",
        amount=100,
        debit_account=AccountingAccount(
            "cash",
            "Cash",
        ),
        credit_account=AccountingAccount(
            "sales",
            "Sales",
        ),
        transaction_class="sales",
        payment_mode="cash",
        ai_confidence=0.9,
        requires_review=False,
        source_text="test",
        normalized_text="test",
    )

    with pytest.raises(ValueError):
        AccountingAdapterResult(
            success=False,
            transaction=transaction,
        )
