from __future__ import annotations

from datetime import datetime

from ml.anomaly_detection.historical_behavior.features import (
    HistoricalBehaviorFeatureEngineer,
)
from ml.anomaly_detection.historical_behavior.schemas import (
    HistoricalBehaviorFeatures,
    HistoricalTransaction,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


def build_historical_features(
    prediction: TransactionPrediction,
    occurred_at: datetime,
    history: tuple[HistoricalTransaction, ...],
) -> HistoricalBehaviorFeatures:
    engineer = HistoricalBehaviorFeatureEngineer()

    return engineer.transform(
        prediction,
        occurred_at,
        history,
    )
