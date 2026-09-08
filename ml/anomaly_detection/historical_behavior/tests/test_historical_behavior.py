from datetime import datetime, timezone

import pytest

from ml.anomaly_detection.historical_behavior.config import (
    HistoricalBehaviorConfig,
)
from ml.anomaly_detection.historical_behavior.features import (
    HistoricalBehaviorFeatureEngineer,
)
from ml.anomaly_detection.historical_behavior.schemas import (
    HistoricalBehaviorFeatures,
    HistoricalTransaction,
)
from ml.transaction_understanding.prediction import (
    PredictionAccount,
    PredictionConfidence,
    PredictionDirection,
    PredictionPaymentMode,
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
    transaction_id="txn-current",
    amount=1000.0,
    transaction_class="sales",
    payment_mode="cash",
):
    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="received cash from customer",
        normalized_text="received cash from customer",
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
        confidence=PredictionConfidence(
            overall=0.93,
            requires_review=False,
            reason="High confidence prediction.",
        ),
    )


def make_history(
    transaction_id,
    occurred_at,
    amount,
    transaction_class="sales",
    payment_mode="cash",
    debit_account_id="cash",
    credit_account_id="sales",
):
    return HistoricalTransaction(
        transaction_id=transaction_id,
        occurred_at=occurred_at,
        amount=amount,
        transaction_class=transaction_class,
        payment_mode=payment_mode,
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id,
    )


def dt(day):
    return datetime(
        2026,
        1,
        day,
        tzinfo=timezone.utc,
    )


def test_config_defaults():
    config = HistoricalBehaviorConfig()

    assert config.minimum_history == 1
    assert config.max_history is None


def test_config_rejects_invalid_minimum_history():
    with pytest.raises(ValueError):
        HistoricalBehaviorConfig(
            minimum_history=-1,
        )


def test_config_rejects_invalid_max_history():
    with pytest.raises(ValueError):
        HistoricalBehaviorConfig(
            max_history=0,
        )


def test_config_rejects_max_history_below_minimum():
    with pytest.raises(ValueError):
        HistoricalBehaviorConfig(
            minimum_history=5,
            max_history=2,
        )


def test_historical_transaction():
    item = make_history(
        "txn-001",
        dt(1),
        100,
    )

    assert item.transaction_id == "txn-001"
    assert item.amount == 100
    assert item.account_pair == "cash->sales"


def test_historical_transaction_requires_timezone():
    with pytest.raises(ValueError):
        make_history(
            "txn-001",
            datetime(2026, 1, 1),
            100,
        )


def test_historical_transaction_rejects_negative_amount():
    with pytest.raises(ValueError):
        make_history(
            "txn-001",
            dt(1),
            -100,
        )


def test_no_history():
    engineer = HistoricalBehaviorFeatureEngineer()

    features = engineer.transform(
        make_prediction(),
        dt(10),
        (),
    )

    assert isinstance(
        features,
        HistoricalBehaviorFeatures,
    )
    assert features.history_count == 0
    assert features.has_history is False
    assert features.amount_mean == 0.0
    assert features.amount_std == 0.0
    assert features.amount_z_score == 0.0


def test_basic_historical_statistics():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), 100),
        make_history("txn-002", dt(2), 200),
        make_history("txn-003", dt(3), 300),
    )

    features = engineer.transform(
        make_prediction(amount=400),
        dt(10),
        history,
    )

    assert features.history_count == 3
    assert features.amount_mean == 200.0
    assert features.amount_min == 100.0
    assert features.amount_max == 300.0
    assert features.amount_deviation_from_mean == 200.0


def test_standard_deviation():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), 100),
        make_history("txn-002", dt(2), 200),
        make_history("txn-003", dt(3), 300),
    )

    features = engineer.transform(
        make_prediction(amount=400),
        dt(10),
        history,
    )

    assert round(features.amount_std, 6) == round(
        81.649658,
        6,
    )


def test_z_score():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), 100),
        make_history("txn-002", dt(2), 200),
        make_history("txn-003", dt(3), 300),
    )

    features = engineer.transform(
        make_prediction(amount=400),
        dt(10),
        history,
    )

    assert round(features.amount_z_score, 6) == round(
        2.44949,
        6,
    )


def test_only_previous_transactions_are_used():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history("txn-before", dt(1), 100),
        make_history("txn-after", dt(20), 999999),
    )

    features = engineer.transform(
        make_prediction(
            transaction_id="txn-current",
            amount=200,
        ),
        dt(10),
        history,
    )

    assert features.history_count == 1
    assert features.amount_mean == 100.0
    assert features.amount_max == 100.0


def test_current_transaction_is_excluded_from_history():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history(
            "txn-current",
            dt(5),
            1000,
        ),
        make_history(
            "txn-before",
            dt(4),
            100,
        ),
    )

    features = engineer.transform(
        make_prediction(
            transaction_id="txn-current",
            amount=1000,
        ),
        dt(5),
        history,
    )

    assert features.history_count == 1
    assert features.amount_mean == 100.0


def test_class_frequency():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history(
            "txn-001",
            dt(1),
            100,
            transaction_class="sales",
        ),
        make_history(
            "txn-002",
            dt(2),
            200,
            transaction_class="sales",
        ),
        make_history(
            "txn-003",
            dt(3),
            300,
            transaction_class="rent",
        ),
    )

    features = engineer.transform(
        make_prediction(
            transaction_class="sales",
        ),
        dt(10),
        history,
    )

    assert features.class_frequency == 2


def test_account_pair_frequency():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history(
            "txn-001",
            dt(1),
            100,
            debit_account_id="cash",
            credit_account_id="sales",
        ),
        make_history(
            "txn-002",
            dt(2),
            200,
            debit_account_id="cash",
            credit_account_id="sales",
        ),
        make_history(
            "txn-003",
            dt(3),
            300,
            debit_account_id="bank",
            credit_account_id="sales",
        ),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.account_pair_frequency == 2


def test_payment_mode_frequency():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history(
            "txn-001",
            dt(1),
            100,
            payment_mode="cash",
        ),
        make_history(
            "txn-002",
            dt(2),
            200,
            payment_mode="cash",
        ),
        make_history(
            "txn-003",
            dt(3),
            300,
            payment_mode="bank_transfer",
        ),
    )

    features = engineer.transform(
        make_prediction(payment_mode="cash"),
        dt(10),
        history,
    )

    assert features.payment_mode_frequency == 2


def test_max_history_limits_history():
    engineer = HistoricalBehaviorFeatureEngineer(
        HistoricalBehaviorConfig(
            max_history=2,
        )
    )

    history = (
        make_history("txn-001", dt(1), 100),
        make_history("txn-002", dt(2), 200),
        make_history("txn-003", dt(3), 300),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.history_count == 2
    assert features.amount_mean == 250.0


def test_duplicate_history_ids_rejected():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), 100),
        make_history("txn-001", dt(2), 200),
    )

    with pytest.raises(ValueError):
        engineer.transform(
            make_prediction(),
            dt(10),
            history,
        )


def test_history_must_be_tuple():
    engineer = HistoricalBehaviorFeatureEngineer()

    with pytest.raises(TypeError):
        engineer.transform(
            make_prediction(),
            dt(10),
            [],
        )


def test_prediction_type_is_validated():
    engineer = HistoricalBehaviorFeatureEngineer()

    with pytest.raises(TypeError):
        engineer.transform(
            "invalid",
            dt(10),
            (),
        )


def test_current_time_requires_timezone():
    engineer = HistoricalBehaviorFeatureEngineer()

    with pytest.raises(ValueError):
        engineer.transform(
            make_prediction(),
            datetime(2026, 1, 10),
            (),
        )


def test_features_are_immutable():
    engineer = HistoricalBehaviorFeatureEngineer()

    features = engineer.transform(
        make_prediction(),
        dt(10),
        (),
    )

    with pytest.raises(AttributeError):
        features.history_count = 10


def test_to_dict():
    engineer = HistoricalBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), 100),
    )

    features = engineer.transform(
        make_prediction(amount=200),
        dt(10),
        history,
    )

    data = features.to_dict()

    assert data["transaction_id"] == "txn-current"
    assert data["history_count"] == 1
    assert data["amount_mean"] == 100.0
    assert data["amount_min"] == 100.0
    assert data["amount_max"] == 100.0
