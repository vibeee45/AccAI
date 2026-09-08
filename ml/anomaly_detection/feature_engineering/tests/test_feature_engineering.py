import pytest

from ml.anomaly_detection.feature_engineering.config import (
    FeatureEngineeringConfig,
)
from ml.anomaly_detection.feature_engineering.features import (
    TransactionFeatureEngineer,
)
from ml.anomaly_detection.feature_engineering.schemas import (
    TransactionFeatures,
)
from ml.transaction_understanding.prediction import (
    PredictionAccount,
    PredictionConfidence,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionSemanticMatch,
    TransactionPrediction,
)


def make_account(
    account_id="cash",
    account_name="Cash",
    confidence=0.95,
):
    return PredictionAccount(
        account_id=account_id,
        account_name=account_name,
        confidence=confidence,
    )


def make_direction(
    account_id="cash",
    account_name="Cash",
    direction="debit",
    confidence=0.95,
):
    return PredictionDirection(
        account_id=account_id,
        account_name=account_name,
        direction=direction,
        confidence=confidence,
        reason="Explicit accounting rule.",
        requires_review=False,
    )


def make_prediction(
    transaction_id="txn-001",
    amount=1000.0,
    normalized_text="received cash from customer",
    transaction_class="sales",
    payment_mode="cash",
    include_semantic_match=False,
    include_overall_confidence=True,
):
    semantic_matches = ()

    if include_semantic_match:
        semantic_matches = (
            PredictionSemanticMatch(
                candidate_id="sales-001",
                candidate_text="cash sale",
                similarity=0.91,
            ),
        )

    confidence = None

    if include_overall_confidence:
        confidence = PredictionConfidence(
            overall=0.93,
            requires_review=False,
            reason="High confidence prediction.",
        )

    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="Original transaction text",
        normalized_text=normalized_text,
        amount=amount,
        transaction_class=transaction_class,
        classification_confidence=0.95,
        debit_account=make_account(
            "cash",
            "Cash",
            0.96,
        ),
        credit_account=make_account(
            "sales",
            "Sales",
            0.94,
        ),
        debit_prediction=make_direction(
            "cash",
            "Cash",
            "debit",
            0.97,
        ),
        credit_prediction=make_direction(
            "sales",
            "Sales",
            "credit",
            0.95,
        ),
        payment_mode=PredictionPaymentMode(
            mode=payment_mode,
            confidence=0.98,
            requires_review=False,
        ),
        semantic_matches=semantic_matches,
        confidence=confidence,
    )


def test_feature_engineer_returns_transaction_features():
    engineer = TransactionFeatureEngineer()
    prediction = make_prediction()

    features = engineer.transform(prediction)

    assert isinstance(features, TransactionFeatures)
    assert features.transaction_id == "txn-001"


def test_basic_numeric_features():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        amount=1000.0,
        normalized_text="received cash from customer",
    )

    features = engineer.transform(prediction)

    assert features.amount == 1000.0
    assert features.log_amount > 0
    assert features.text_length == len(
        "received cash from customer"
    )
    assert features.word_count == 4


def test_transaction_class_feature():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        transaction_class="sales",
    )

    features = engineer.transform(prediction)

    assert features.transaction_class == "sales"


def test_payment_mode_feature():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        payment_mode="cash",
    )

    features = engineer.transform(prediction)

    assert features.payment_mode == "cash"


def test_account_features():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction()

    features = engineer.transform(prediction)

    assert features.debit_account_id == "cash"
    assert features.credit_account_id == "sales"
    assert features.account_pair == "cash->sales"


def test_confidence_features():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        include_overall_confidence=True,
    )

    features = engineer.transform(prediction)

    assert features.classification_confidence == 0.95
    assert features.debit_account_confidence == 0.96
    assert features.credit_account_confidence == 0.94
    assert features.debit_direction_confidence == 0.97
    assert features.credit_direction_confidence == 0.95
    assert features.payment_mode_confidence == 0.98
    assert features.overall_confidence == 0.93


def test_semantic_features_when_match_exists():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        include_semantic_match=True,
    )

    features = engineer.transform(prediction)

    assert features.has_semantic_match is True
    assert features.semantic_similarity == 0.91


def test_semantic_features_without_match():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        include_semantic_match=False,
    )

    features = engineer.transform(prediction)

    assert features.has_semantic_match is False
    assert features.semantic_similarity == 0.0


def test_overall_confidence_defaults_to_none():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        include_overall_confidence=False,
    )

    features = engineer.transform(prediction)

    assert features.overall_confidence is None


def test_missing_amount_becomes_zero():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction(
        amount=None,
    )

    features = engineer.transform(prediction)

    assert features.amount == 0.0
    assert features.log_amount == 0.0


def test_numeric_vector_contains_expected_values():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction()

    features = engineer.transform(prediction)

    vector = features.numeric_vector

    assert isinstance(vector, tuple)
    assert len(vector) > 0
    assert vector[0] == features.amount


def test_categorical_features_are_available():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction()

    features = engineer.transform(prediction)

    categorical = features.categorical_features

    assert isinstance(categorical, dict)
    assert categorical["transaction_class"] == "sales"
    assert categorical["payment_mode"] == "cash"
    assert categorical["debit_account_id"] == "cash"
    assert categorical["credit_account_id"] == "sales"
    assert categorical["account_pair"] == "cash->sales"


def test_to_dict_contains_transaction_features():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction()

    features = engineer.transform(prediction)

    data = features.to_dict()

    assert isinstance(data, dict)
    assert data["transaction_id"] == "txn-001"
    assert data["amount"] == 1000.0
    assert data["transaction_class"] == "sales"
    assert data["payment_mode"] == "cash"
    assert data["account_pair"] == "cash->sales"


def test_transform_many():
    engineer = TransactionFeatureEngineer()

    first = make_prediction(
        transaction_id="txn-001",
    )

    second = make_prediction(
        transaction_id="txn-002",
        amount=2500.0,
        transaction_class="rent",
        payment_mode="bank_transfer",
    )

    result = engineer.transform_many(
        (first, second)
    )

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0].transaction_id == "txn-001"
    assert result[1].transaction_id == "txn-002"


def test_transform_many_rejects_duplicate_transaction_ids():
    engineer = TransactionFeatureEngineer()

    first = make_prediction(
        transaction_id="txn-001",
    )

    second = make_prediction(
        transaction_id="txn-001",
    )

    with pytest.raises(ValueError):
        engineer.transform_many(
            (first, second)
        )


def test_features_are_immutable():
    engineer = TransactionFeatureEngineer()

    prediction = make_prediction()

    features = engineer.transform(prediction)

    with pytest.raises(AttributeError):
        features.amount = 5000.0


def test_config_defaults():
    config = FeatureEngineeringConfig()

    assert config.log_amount_offset == 1.0
    assert config.min_text_length == 0
    assert config.min_word_count == 0


def test_config_rejects_non_positive_log_offset():
    with pytest.raises(ValueError):
        FeatureEngineeringConfig(
            log_amount_offset=0,
        )


@pytest.mark.parametrize(
    "value",
    [-1, -10],
)
def test_config_rejects_negative_min_text_length(value):
    with pytest.raises(ValueError):
        FeatureEngineeringConfig(
            min_text_length=value,
        )


@pytest.mark.parametrize(
    "value",
    [-1, -10],
)
def test_config_rejects_negative_min_word_count(value):
    with pytest.raises(ValueError):
        FeatureEngineeringConfig(
            min_word_count=value,
        )


