from __future__ import annotations

from datetime import datetime, timedelta

from ml.anomaly_detection.transaction_velocity.config import (
    TransactionVelocityConfig,
)
from ml.anomaly_detection.transaction_velocity.schemas import (
    TransactionVelocityFeatures,
    VelocityHistoryItem,
)
from ml.transaction_understanding.prediction.schemas import TransactionPrediction


class TransactionVelocityFeatureEngineer:
    """Calculate transaction-frequency and velocity features."""

    def __init__(
        self,
        config: TransactionVelocityConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else TransactionVelocityConfig()
        )

    def transform(
        self,
        prediction: TransactionPrediction,
        occurred_at: datetime,
        history: tuple[VelocityHistoryItem, ...],
    ) -> TransactionVelocityFeatures:
        if not isinstance(prediction, TransactionPrediction):
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
            occurred_at,
            relevant_history,
        )

    @staticmethod
    def _previous_history(
        transaction_id: str,
        occurred_at: datetime,
        history: tuple[VelocityHistoryItem, ...],
    ) -> tuple[VelocityHistoryItem, ...]:
        """Return only transactions occurring before the current one."""

        # Validate item types BEFORE accessing their attributes.
        for item in history:
            if not isinstance(item, VelocityHistoryItem):
                raise TypeError(
                    "history must contain VelocityHistoryItem objects."
                )

        ids = [item.transaction_id for item in history]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "history contains duplicate transaction IDs."
            )

        return tuple(
            item
            for item in history
            if item.transaction_id != transaction_id
            and item.occurred_at < occurred_at
        )

    def _build_features(
        self,
        prediction: TransactionPrediction,
        occurred_at: datetime,
        history: tuple[VelocityHistoryItem, ...],
    ) -> TransactionVelocityFeatures:

        if not history:
            return TransactionVelocityFeatures(
                transaction_id=prediction.transaction_id,
                history_count=0,
                transactions_last_1h=0,
                transactions_last_24h=0,
                transactions_last_7d=0,
                time_since_previous_seconds=0.0,
                hourly_rate=0.0,
                daily_rate=0.0,
                weekly_rate=0.0,
                unique_active_days=0,
                velocity_ratio=0.0,
                velocity_anomaly=False,
            )

        short_cutoff = (
            occurred_at
            - timedelta(
                seconds=self.config.short_window_seconds
            )
        )

        daily_cutoff = (
            occurred_at
            - timedelta(
                seconds=self.config.daily_window_seconds
            )
        )

        weekly_cutoff = (
            occurred_at
            - timedelta(
                seconds=self.config.weekly_window_seconds
            )
        )

        transactions_last_1h = sum(
            item.occurred_at >= short_cutoff
            for item in history
        )

        transactions_last_24h = sum(
            item.occurred_at >= daily_cutoff
            for item in history
        )

        transactions_last_7d = sum(
            item.occurred_at >= weekly_cutoff
            for item in history
        )

        previous_transaction = max(
            history,
            key=lambda item: item.occurred_at,
        )

        time_since_previous_seconds = (
            occurred_at
            - previous_transaction.occurred_at
        ).total_seconds()

        # Transactions per hour.
        hourly_rate = (
            transactions_last_1h
            / (self.config.short_window_seconds / 3600)
        )

        # Transactions per day.
        daily_rate = (
            transactions_last_24h
            / (self.config.daily_window_seconds / 86400)
        )

        # Average transactions per day across the 7-day window.
        weekly_rate = (
            transactions_last_7d
            / (self.config.weekly_window_seconds / 86400)
        )

        unique_active_days = len(
            {
                item.occurred_at.date()
                for item in history
                if item.occurred_at >= weekly_cutoff
            }
        )

        # Compare today's activity against the historical
        # average daily frequency over the 7-day window.
        historical_average_daily_frequency = (
            transactions_last_7d / 7
        )

        current_daily_frequency = transactions_last_24h

        if historical_average_daily_frequency > 0:
            velocity_ratio = (
                current_daily_frequency
                / historical_average_daily_frequency
            )
        else:
            velocity_ratio = 0.0

        # Basic rule-based anomaly flag.
        velocity_anomaly = (
            transactions_last_1h >= 5
            or velocity_ratio >= 3.0
        )

        return TransactionVelocityFeatures(
            transaction_id=prediction.transaction_id,
            history_count=len(history),
            transactions_last_1h=transactions_last_1h,
            transactions_last_24h=transactions_last_24h,
            transactions_last_7d=transactions_last_7d,
            time_since_previous_seconds=time_since_previous_seconds,
            hourly_rate=hourly_rate,
            daily_rate=daily_rate,
            weekly_rate=weekly_rate,
            unique_active_days=unique_active_days,
            velocity_ratio=velocity_ratio,
            velocity_anomaly=velocity_anomaly,
        )
