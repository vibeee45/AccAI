from __future__ import annotations

import math
from collections import Counter
from datetime import datetime

from ml.anomaly_detection.historical_behavior.config import (
    HistoricalBehaviorConfig,
)
from ml.anomaly_detection.historical_behavior.schemas import (
    HistoricalBehaviorFeatures,
    HistoricalTransaction,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


class HistoricalBehaviorFeatureEngineer:
    """Calculate historical transaction behavior without data leakage."""

    def __init__(
        self,
        config: HistoricalBehaviorConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else HistoricalBehaviorConfig()
        )

    def transform(
        self,
        prediction: TransactionPrediction,
        occurred_at: datetime,
        history: tuple[HistoricalTransaction, ...],
    ) -> HistoricalBehaviorFeatures:
        if not isinstance(
            prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        if occurred_at.tzinfo is None:
            raise ValueError(
                "occurred_at must be timezone-aware."
            )

        if not isinstance(history, tuple):
            raise TypeError(
                "history must be a tuple."
            )

        relevant_history = self._previous_history(
            prediction.transaction_id,
            occurred_at,
            history,
        )

        if self.config.max_history is not None:
            relevant_history = relevant_history[
                -self.config.max_history:
            ]

        return self._build_features(
            prediction,
            relevant_history,
        )

    @staticmethod
    def _previous_history(
        transaction_id: str,
        occurred_at: datetime,
        history: tuple[HistoricalTransaction, ...],
    ) -> tuple[HistoricalTransaction, ...]:
        ids = [item.transaction_id for item in history]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "history contains duplicate transaction IDs."
            )

        for item in history:
            if not isinstance(
                item,
                HistoricalTransaction,
            ):
                raise TypeError(
                    "history must contain HistoricalTransaction objects."
                )

        return tuple(
            item
            for item in history
            if item.transaction_id != transaction_id
            and item.occurred_at < occurred_at
        )

    @staticmethod
    def _build_features(
        prediction: TransactionPrediction,
        history: tuple[HistoricalTransaction, ...],
    ) -> HistoricalBehaviorFeatures:
        amounts = [item.amount for item in history]

        if not amounts:
            return HistoricalBehaviorFeatures(
                transaction_id=prediction.transaction_id,
                history_count=0,
                amount_mean=0.0,
                amount_std=0.0,
                amount_min=0.0,
                amount_max=0.0,
                amount_deviation_from_mean=0.0,
                amount_z_score=0.0,
                class_frequency=0,
                account_pair_frequency=0,
                payment_mode_frequency=0,
            )

        mean = sum(amounts) / len(amounts)

        variance = sum(
            (amount - mean) ** 2
            for amount in amounts
        ) / len(amounts)

        std = math.sqrt(variance)

        amount = (
            float(prediction.amount)
            if prediction.amount is not None
            else 0.0
        )

        deviation = abs(amount - mean)

        z_score = (
            deviation / std
            if std > 0
            else 0.0
        )

        account_pair = (
            f"{prediction.debit_account.account_id}"
            f"->{prediction.credit_account.account_id}"
        )

        class_frequency = sum(
            item.transaction_class
            == prediction.transaction_class
            for item in history
        )

        account_pair_frequency = sum(
            item.account_pair == account_pair
            for item in history
        )

        payment_mode_frequency = sum(
            item.payment_mode
            == prediction.payment_mode.mode
            for item in history
        )

        return HistoricalBehaviorFeatures(
            transaction_id=prediction.transaction_id,
            history_count=len(history),
            amount_mean=mean,
            amount_std=std,
            amount_min=min(amounts),
            amount_max=max(amounts),
            amount_deviation_from_mean=deviation,
            amount_z_score=z_score,
            class_frequency=class_frequency,
            account_pair_frequency=account_pair_frequency,
            payment_mode_frequency=payment_mode_frequency,
        )
