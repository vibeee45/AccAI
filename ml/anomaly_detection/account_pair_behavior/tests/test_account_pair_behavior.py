from datetime import datetime, timezone

import pytest

from ml.anomaly_detection.account_pair_behavior.config import (
    AccountPairBehaviorConfig,
)
from ml.anomaly_detection.account_pair_behavior.features import (
    AccountPairBehaviorFeatureEngineer,
)
from ml.anomaly_detection.account_pair_behavior.schemas import (
    AccountPairBehaviorFeatures,
    AccountPairHistoryItem,
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
    debit_account_id="cash",
    credit_account_id="sales",
):
    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="received cash from customer",
        normalized_text="received cash from customer",
        amount=1000.0,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=make_account(
            debit_account_id,
            "Debit Account",
            0.96,
        ),
        credit_account=make_account(
            credit_account_id,
            "Credit Account",
            0.94,
        ),
        debit_prediction=make_direction(
            debit_account_id,
            "Debit Account",
            "debit",
            0.97,
        ),
        credit_prediction=make_direction(
            credit_account_id,
            "Credit Account",
            "credit",
            0.95,
        ),
        payment_mode=PredictionPaymentMode(
            mode="cash",
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
    debit_account_id="cash",
    credit_account_id="sales",
):
    return AccountPairHistoryItem(
        transaction_id=transaction_id,
        occurred_at=occurred_at,
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
    config = AccountPairBehaviorConfig()

    assert config.max_history is None


def test_config_rejects_invalid_max_history():
    with pytest.raises(ValueError):
        AccountPairBehaviorConfig(max_history=0)


def test_history_item():
    item = make_history(
        "txn-001",
        dt(1),
    )

    assert item.account_pair == "cash->sales"


def test_history_item_requires_timezone():
    with pytest.raises(ValueError):
        make_history(
            "txn-001",
            datetime(2026, 1, 1),
        )


def test_history_item_rejects_same_accounts():
    with pytest.raises(ValueError):
        make_history(
            "txn-001",
            dt(1),
            "cash",
            "cash",
        )


def test_no_history():
    engineer = AccountPairBehaviorFeatureEngineer()

    features = engineer.transform(
        make_prediction(),
        dt(10),
        (),
    )

    assert isinstance(
        features,
        AccountPairBehaviorFeatures,
    )
    assert features.history_count == 0
    assert features.pair_frequency == 0
    assert features.pair_ratio == 0.0
    assert features.unique_pair_count == 0
    assert features.pair_seen_before is False


def test_pair_frequency():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), "cash", "sales"),
        make_history("txn-002", dt(2), "cash", "sales"),
        make_history("txn-003", dt(3), "bank", "sales"),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.history_count == 3
    assert features.pair_frequency == 2
    assert features.pair_seen_before is True


def test_pair_ratio():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), "cash", "sales"),
        make_history("txn-002", dt(2), "cash", "sales"),
        make_history("txn-003", dt(3), "bank", "sales"),
        make_history("txn-004", dt(4), "cash", "rent"),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.pair_frequency == 2
    assert features.pair_ratio == 0.5


def test_unique_pair_count():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), "cash", "sales"),
        make_history("txn-002", dt(2), "cash", "sales"),
        make_history("txn-003", dt(3), "bank", "sales"),
        make_history("txn-004", dt(4), "cash", "rent"),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.unique_pair_count == 3


def test_unseen_pair():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1), "cash", "sales"),
        make_history("txn-002", dt(2), "bank", "sales"),
    )

    features = engineer.transform(
        make_prediction(
            debit_account_id="inventory",
            credit_account_id="supplier",
        ),
        dt(10),
        history,
    )

    assert features.pair_frequency == 0
    assert features.pair_ratio == 0.0
    assert features.pair_seen_before is False


def test_only_previous_transactions_are_used():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history("txn-before", dt(1), "cash", "sales"),
        make_history("txn-after", dt(20), "cash", "sales"),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.history_count == 1
    assert features.pair_frequency == 1


def test_current_transaction_is_excluded():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history(
            "txn-current",
            dt(5),
            "cash",
            "sales",
        ),
        make_history(
            "txn-before",
            dt(4),
            "bank",
            "sales",
        ),
    )

    features = engineer.transform(
        make_prediction(),
        dt(5),
        history,
    )

    assert features.history_count == 1
    assert features.pair_frequency == 0


def test_duplicate_history_ids_rejected():
    engineer = AccountPairBehaviorFeatureEngineer()

    history = (
        make_history("txn-001", dt(1)),
        make_history("txn-001", dt(2)),
    )

    with pytest.raises(ValueError):
        engineer.transform(
            make_prediction(),
            dt(10),
            history,
        )


def test_history_must_be_tuple():
    engineer = AccountPairBehaviorFeatureEngineer()

    with pytest.raises(TypeError):
        engineer.transform(
            make_prediction(),
            dt(10),
            [],
        )


def test_prediction_type_is_validated():
    engineer = AccountPairBehaviorFeatureEngineer()

    with pytest.raises(TypeError):
        engineer.transform(
            "invalid",
            dt(10),
            (),
        )


def test_current_time_requires_timezone():
    engineer = AccountPairBehaviorFeatureEngineer()

    with pytest.raises(ValueError):
        engineer.transform(
            make_prediction(),
            datetime(2026, 1, 10),
            (),
        )


def test_max_history():
    engineer = AccountPairBehaviorFeatureEngineer(
        AccountPairBehaviorConfig(max_history=2)
    )

    history = (
        make_history("txn-001", dt(1), "cash", "sales"),
        make_history("txn-002", dt(2), "bank", "sales"),
        make_history("txn-003", dt(3), "cash", "sales"),
    )

    features = engineer.transform(
        make_prediction(),
        dt(10),
        history,
    )

    assert features.history_count == 2
    assert features.pair_frequency == 1


def test_features_are_immutable():
    engineer = AccountPairBehaviorFeatureEngineer()

    features = engineer.transform(
        make_prediction(),
        dt(10),
        (),
    )

    with pytest.raises(AttributeError):
        features.pair_frequency = 10


def test_to_dict():
    engineer = AccountPairBehaviorFeatureEngineer()

    features = engineer.transform(
        make_prediction(),
        dt(10),
        (
            make_history("txn-001", dt(1)),
        ),
    )

    data = features.to_dict()

    assert data["transaction_id"] == "txn-current"
    assert data["account_pair"] == "cash->sales"
    assert data["history_count"] == 1
    assert data["pair_frequency"] == 1
    assert data["pair_ratio"] == 1.0
    assert data["unique_pair_count"] == 1
    assert data["pair_seen_before"] is True
