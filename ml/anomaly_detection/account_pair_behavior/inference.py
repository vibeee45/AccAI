from __future__ import annotations

from datetime import datetime

from ml.anomaly_detection.account_pair_behavior.features import (
    AccountPairBehaviorFeatureEngineer,
)
from ml.anomaly_detection.account_pair_behavior.schemas import (
    AccountPairBehaviorFeatures,
    AccountPairHistoryItem,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


def build_account_pair_features(
    prediction: TransactionPrediction,
    occurred_at: datetime,
    history: tuple[AccountPairHistoryItem, ...],
) -> AccountPairBehaviorFeatures:
    engineer = AccountPairBehaviorFeatureEngineer()

    return engineer.transform(
        prediction,
        occurred_at,
        history,
    )
