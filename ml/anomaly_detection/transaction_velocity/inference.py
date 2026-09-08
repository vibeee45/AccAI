from __future__ import annotations

from datetime import datetime

from ml.anomaly_detection.transaction_velocity.features import (
    TransactionVelocityFeatureEngineer,
)
from ml.anomaly_detection.transaction_velocity.schemas import (
    TransactionVelocityFeatures,
    VelocityHistoryItem,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


def build_transaction_velocity_features(
    prediction: TransactionPrediction,
    occurred_at: datetime,
    history: tuple[VelocityHistoryItem, ...],
) -> TransactionVelocityFeatures:
    """Build transaction velocity features using the default configuration."""

    engineer = TransactionVelocityFeatureEngineer()

    return engineer.transform(
        prediction=prediction,
        occurred_at=occurred_at,
        history=history,
    )
