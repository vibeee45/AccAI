from __future__ import annotations

import math

from ml.anomaly_detection.feature_engineering.config import (
    FeatureEngineeringConfig,
)
from ml.anomaly_detection.feature_engineering.schemas import (
    TransactionFeatures,
)
from ml.transaction_understanding.prediction.schemas import (
    TransactionPrediction,
)


class TransactionFeatureEngineer:
    """Build deterministic anomaly-detection features."""

    def __init__(
        self,
        config: FeatureEngineeringConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else FeatureEngineeringConfig()
        )

    def transform(
        self,
        prediction: TransactionPrediction,
    ) -> TransactionFeatures:
        if not isinstance(
            prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        amount = (
            float(prediction.amount)
            if prediction.amount is not None
            else 0.0
        )

        text = prediction.normalized_text.strip()

        text_length = len(text)
        word_count = len(text.split())

        semantic_similarity = self._semantic_similarity(
            prediction
        )

        overall_confidence = (
            prediction.confidence.overall
            if prediction.confidence is not None
            else None
        )

        account_pair = (
            f"{prediction.debit_account.account_id}"
            f"->{prediction.credit_account.account_id}"
        )

        return TransactionFeatures(
            transaction_id=prediction.transaction_id,
            amount=amount,
            log_amount=math.log(
                amount + self.config.log_amount_offset
            ),
            transaction_class=(
                prediction.transaction_class
            ),
            payment_mode=prediction.payment_mode.mode,
            debit_account_id=(
                prediction.debit_account.account_id
            ),
            debit_account_name=(
                prediction.debit_account.account_name
            ),
            credit_account_id=(
                prediction.credit_account.account_id
            ),
            credit_account_name=(
                prediction.credit_account.account_name
            ),
            account_pair=account_pair,
            text_length=text_length,
            word_count=word_count,
            has_semantic_match=bool(
                prediction.semantic_matches
            ),
            semantic_similarity=semantic_similarity,
            classification_confidence=(
                prediction.classification_confidence
            ),
            debit_account_confidence=(
                prediction.debit_account.confidence
            ),
            credit_account_confidence=(
                prediction.credit_account.confidence
            ),
            debit_direction_confidence=(
                prediction.debit_prediction.confidence
            ),
            credit_direction_confidence=(
                prediction.credit_prediction.confidence
            ),
            payment_mode_confidence=(
                prediction.payment_mode.confidence
            ),
            overall_confidence=overall_confidence,
            metadata=dict(prediction.metadata),
        )

    def transform_many(
        self,
        predictions: tuple[
            TransactionPrediction,
            ...,
        ],
    ) -> tuple[TransactionFeatures, ...]:
        if not isinstance(predictions, tuple):
            raise TypeError(
                "predictions must be a tuple."
            )

        transaction_ids = [
            prediction.transaction_id
            for prediction in predictions
        ]

        if len(transaction_ids) != len(
            set(transaction_ids)
        ):
            raise ValueError(
                "predictions contain duplicate transaction IDs."
            )

        return tuple(
            self.transform(prediction)
            for prediction in predictions
        )

    @staticmethod
    def _semantic_similarity(
        prediction: TransactionPrediction,
    ) -> float:
        if not prediction.semantic_matches:
            return 0.0

        return max(
            match.similarity
            for match in prediction.semantic_matches
        )
