from __future__ import annotations

from ml.anomaly_detection.feature_engineering.features import (
    TransactionFeatureEngineer,
)
from ml.anomaly_detection.feature_engineering.schemas import (
    TransactionFeatures,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


def engineer_features(
    prediction: TransactionPrediction,
) -> TransactionFeatures:
    """Engineer anomaly features for one transaction."""

    return TransactionFeatureEngineer().transform(
        prediction
    )


def engineer_features_batch(
    predictions: tuple[
        TransactionPrediction,
        ...,
    ],
) -> tuple[TransactionFeatures, ...]:
    """Engineer anomaly features for a transaction batch."""

    return TransactionFeatureEngineer().transform_many(
        predictions
    )
