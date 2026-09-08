from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ml.anomaly_detection.transaction_velocity.config import (
    TransactionVelocityConfig,
)
from ml.anomaly_detection.transaction_velocity.features import (
    TransactionVelocityFeatureEngineer,
)
from ml.anomaly_detection.transaction_velocity.schemas import (
    TransactionVelocityFeatures,
    VelocityHistoryItem,
)
from ml.transaction_understanding.prediction.schemas import (
    PredictionAccount,
    PredictionDirection,
    PredictionPaymentMode,
    TransactionPrediction,
)


UTC = timezone.utc


def make_prediction(
    transaction_id: str = "tx-current",
) -> TransactionPrediction:
    """Create a valid TransactionPrediction for testing."""

    debit_account = PredictionAccount(
        account_id="expense-001",
        account_name="Expense",
        confidence=0.95,
    )

    credit_account = PredictionAccount(
        account_id="bank-001",
        account_name="Bank",
        confidence=0.95,
    )

    debit_prediction = PredictionDirection(
        account_id="expense-001",
        account_name="Expense",
        direction="debit",
        confidence=0.95,
        reason="Expense transaction",
        requires_review=False,
    )

    credit_prediction = PredictionDirection(
        account_id="bank-001",
        account_name="Bank",
        direction="credit",
        confidence=0.95,
        reason="Bank payment",
        requires_review=False,
    )

    payment_mode = PredictionPaymentMode(
        mode="bank_transfer",
        confidence=0.95,
        requires_review=False,
    )

    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="Paid supplier by bank transfer",
        normalized_text="paid supplier by bank transfer",
        amount=1000.0,
        transaction_class="expense",
        classification_confidence=0.95,
        debit_account=debit_account,
        credit_account=credit_account,
        debit_prediction=debit_prediction,
        credit_prediction=credit_prediction,
        payment_mode=payment_mode,
    )


def history_item(
    transaction_id: str,
    occurred_at: datetime,
) -> VelocityHistoryItem:
    return VelocityHistoryItem(
        transaction_id=transaction_id,
        occurred_at=occurred_at,
    )


def test_config_defaults() -> None:
    config = TransactionVelocityConfig()

    assert config.short_window_seconds == 3600
    assert config.daily_window_seconds == 86400
    assert config.weekly_window_seconds == 604800
    assert config.max_history is None


def test_config_rejects_invalid_short_window() -> None:
    with pytest.raises(ValueError):
        TransactionVelocityConfig(
            short_window_seconds=0,
        )


def test_config_rejects_invalid_daily_window() -> None:
    with pytest.raises(ValueError):
        TransactionVelocityConfig(
            daily_window_seconds=0,
        )


def test_config_rejects_invalid_weekly_window() -> None:
    with pytest.raises(ValueError):
        TransactionVelocityConfig(
            weekly_window_seconds=0,
        )


def test_config_rejects_invalid_window_order() -> None:
    with pytest.raises(ValueError):
        TransactionVelocityConfig(
            short_window_seconds=100,
            daily_window_seconds=50,
        )


def test_config_rejects_invalid_max_history() -> None:
    with pytest.raises(ValueError):
        TransactionVelocityConfig(
            max_history=0,
        )


def test_history_item() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    item = VelocityHistoryItem(
        transaction_id="tx-001",
        occurred_at=occurred_at,
    )

    assert item.transaction_id == "tx-001"
    assert item.occurred_at == occurred_at


def test_history_item_requires_timezone() -> None:
    with pytest.raises(ValueError):
        VelocityHistoryItem(
            transaction_id="tx-001",
            occurred_at=datetime(2026, 9, 9, 15, 0),
        )


def test_empty_history() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        (),
    )

    assert features.history_count == 0
    assert features.transactions_last_1h == 0
    assert features.transactions_last_24h == 0
    assert features.transactions_last_7d == 0
    assert features.time_since_previous_seconds == 0.0
    assert features.hourly_rate == 0.0
    assert features.daily_rate == 0.0
    assert features.weekly_rate == 0.0
    assert features.unique_active_days == 0
    assert features.velocity_ratio == 0.0
    assert features.velocity_anomaly is False


def test_previous_transactions_are_counted() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(minutes=10),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(hours=2),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.history_count == 2
    assert features.transactions_last_1h == 1
    assert features.transactions_last_24h == 2
    assert features.transactions_last_7d == 2


def test_last_1h_window() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(minutes=30),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(minutes=59),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(hours=2),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.transactions_last_1h == 2


def test_last_24h_window() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(hours=2),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(hours=23),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(hours=25),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.transactions_last_24h == 2


def test_last_7d_window() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(days=1),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(days=6),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(days=8),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.transactions_last_7d == 2


def test_current_transaction_is_excluded() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-current",
            occurred_at,
        ),
        history_item(
            "tx-001",
            occurred_at - timedelta(minutes=10),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction("tx-current"),
        occurred_at,
        history,
    )

    assert features.history_count == 1
    assert features.transactions_last_1h == 1


def test_future_transactions_are_excluded() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-before",
            occurred_at - timedelta(minutes=10),
        ),
        history_item(
            "tx-future",
            occurred_at + timedelta(minutes=10),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.history_count == 1


def test_time_since_previous_transaction() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-old",
            occurred_at - timedelta(hours=5),
        ),
        history_item(
            "tx-latest",
            occurred_at - timedelta(minutes=30),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.time_since_previous_seconds == 1800.0


def test_no_previous_transaction_has_zero_time_gap() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        (),
    )

    assert features.time_since_previous_seconds == 0.0


def test_rates_are_calculated() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(minutes=10),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(hours=2),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(days=2),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.hourly_rate == pytest.approx(1.0)
    assert features.daily_rate == pytest.approx(2.0)
    assert features.weekly_rate == pytest.approx(3.0 / 7.0)


def test_unique_active_days() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(hours=1),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(hours=2),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(days=1),
        ),
        history_item(
            "tx-004",
            occurred_at - timedelta(days=2),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.unique_active_days == 3


def test_velocity_ratio() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(hours=1),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(hours=2),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(days=2),
        ),
        history_item(
            "tx-004",
            occurred_at - timedelta(days=3),
        ),
        history_item(
            "tx-005",
            occurred_at - timedelta(days=4),
        ),
        history_item(
            "tx-006",
            occurred_at - timedelta(days=5),
        ),
        history_item(
            "tx-007",
            occurred_at - timedelta(days=6),
        ),
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.velocity_ratio == pytest.approx(2.0)


def test_high_recent_activity_is_anomaly() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = tuple(
        history_item(
            f"tx-{index}",
            occurred_at - timedelta(minutes=index * 5),
        )
        for index in range(1, 6)
    )

    features = TransactionVelocityFeatureEngineer().transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.transactions_last_1h == 5
    assert features.velocity_anomaly is True


def test_history_must_be_tuple() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    with pytest.raises(TypeError):
        TransactionVelocityFeatureEngineer().transform(
            make_prediction(),
            occurred_at,
            [],
        )


def test_prediction_type_is_validated() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    with pytest.raises(TypeError):
        TransactionVelocityFeatureEngineer().transform(
            "invalid",
            occurred_at,
            (),
        )


def test_current_time_requires_timezone() -> None:
    with pytest.raises(ValueError):
        TransactionVelocityFeatureEngineer().transform(
            make_prediction(),
            datetime(2026, 9, 9, 15, 0),
            (),
        )


def test_duplicate_history_ids_are_rejected() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "duplicate",
            occurred_at - timedelta(minutes=10),
        ),
        history_item(
            "duplicate",
            occurred_at - timedelta(minutes=20),
        ),
    )

    with pytest.raises(ValueError):
        TransactionVelocityFeatureEngineer().transform(
            make_prediction(),
            occurred_at,
            history,
        )


def test_invalid_history_item_type_is_rejected() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    with pytest.raises(TypeError):
        TransactionVelocityFeatureEngineer().transform(
            make_prediction(),
            occurred_at,
            ("invalid",),
        )


def test_max_history() -> None:
    occurred_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    history = (
        history_item(
            "tx-001",
            occurred_at - timedelta(hours=3),
        ),
        history_item(
            "tx-002",
            occurred_at - timedelta(hours=2),
        ),
        history_item(
            "tx-003",
            occurred_at - timedelta(hours=1),
        ),
    )

    config = TransactionVelocityConfig(
        max_history=2,
    )

    features = TransactionVelocityFeatureEngineer(
        config
    ).transform(
        make_prediction(),
        occurred_at,
        history,
    )

    assert features.history_count == 2
    assert features.transactions_last_1h == 1


def test_features_are_immutable() -> None:
    features = TransactionVelocityFeatures(
        transaction_id="tx-001",
        history_count=1,
        transactions_last_1h=1,
        transactions_last_24h=1,
        transactions_last_7d=1,
        time_since_previous_seconds=60.0,
        hourly_rate=1.0,
        daily_rate=1.0,
        weekly_rate=1.0,
        unique_active_days=1,
        velocity_ratio=1.0,
        velocity_anomaly=False,
    )

    with pytest.raises(AttributeError):
        features.history_count = 10


def test_to_dict() -> None:
    features = TransactionVelocityFeatures(
        transaction_id="tx-001",
        history_count=2,
        transactions_last_1h=1,
        transactions_last_24h=2,
        transactions_last_7d=2,
        time_since_previous_seconds=120.0,
        hourly_rate=1.0,
        daily_rate=2.0,
        weekly_rate=2.0 / 7.0,
        unique_active_days=2,
        velocity_ratio=1.5,
        velocity_anomaly=False,
    )

    result = features.to_dict()

    assert result["transaction_id"] == "tx-001"
    assert result["history_count"] == 2
    assert result["transactions_last_1h"] == 1
    assert result["transactions_last_24h"] == 2
    assert result["transactions_last_7d"] == 2
    assert result["time_since_previous_seconds"] == 120.0
    assert result["velocity_anomaly"] is False
