from __future__ import annotations

from datetime import datetime

from ml.anomaly_detection.account_pair_behavior.config import (
    AccountPairBehaviorConfig,
)
from ml.anomaly_detection.account_pair_behavior.schemas import (
    AccountPairBehaviorFeatures,
    AccountPairHistoryItem,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


class AccountPairBehaviorFeatureEngineer:
    """Calculate historical account-pair behavior without leakage."""

    def __init__(
        self,
        config: AccountPairBehaviorConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else AccountPairBehaviorConfig()
        )

    def transform(
        self,
        prediction: TransactionPrediction,
        occurred_at: datetime,
        history: tuple[AccountPairHistoryItem, ...],
    ) -> AccountPairBehaviorFeatures:
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

        account_pair = (
            f"{prediction.debit_account.account_id}"
            f"->{prediction.credit_account.account_id}"
        )

        history_count = len(relevant_history)

        pair_frequency = sum(
            item.account_pair == account_pair
            for item in relevant_history
        )

        unique_pairs = {
            item.account_pair
            for item in relevant_history
        }

        pair_ratio = (
            pair_frequency / history_count
            if history_count > 0
            else 0.0
        )

        return AccountPairBehaviorFeatures(
            transaction_id=prediction.transaction_id,
            account_pair=account_pair,
            history_count=history_count,
            pair_frequency=pair_frequency,
            pair_ratio=pair_ratio,
            unique_pair_count=len(unique_pairs),
            pair_seen_before=pair_frequency > 0,
        )

    @staticmethod
    def _previous_history(
        transaction_id: str,
        occurred_at: datetime,
        history: tuple[AccountPairHistoryItem, ...],
    ) -> tuple[AccountPairHistoryItem, ...]:
        ids = [item.transaction_id for item in history]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "history contains duplicate transaction IDs."
            )

        for item in history:
            if not isinstance(
                item,
                AccountPairHistoryItem,
            ):
                raise TypeError(
                    "history must contain "
                    "AccountPairHistoryItem objects."
                )

        return tuple(
            item
            for item in history
            if (
                item.transaction_id != transaction_id
                and item.occurred_at < occurred_at
            )
        )
