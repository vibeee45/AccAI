from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

from ml.transaction_understanding.prediction import (
    PredictionStatus,
    TransactionPrediction,
)

from .config import StructuredOutputConfig
from .schemas import (
    StructuredAccount,
    StructuredConfidence,
    StructuredDirection,
    StructuredPaymentMode,
    StructuredSemanticMatch,
    StructuredTransaction,
)


class StructuredOutputSerializer:
    def __init__(
        self,
        config: StructuredOutputConfig | None = None,
    ) -> None:
        self.config = (
            config
            or StructuredOutputConfig()
        )

    def serialize(
        self,
        prediction: TransactionPrediction,
    ) -> StructuredTransaction:
        if not isinstance(
            prediction,
            TransactionPrediction,
        ):
            raise TypeError(
                "prediction must be TransactionPrediction."
            )

        debit_account = StructuredAccount(
            account_id=(
                prediction.debit_account.account_id
            ),
            account_name=(
                prediction.debit_account.account_name
            ),
            confidence=(
                prediction.debit_account.confidence
            ),
        )

        credit_account = StructuredAccount(
            account_id=(
                prediction.credit_account.account_id
            ),
            account_name=(
                prediction.credit_account.account_name
            ),
            confidence=(
                prediction.credit_account.confidence
            ),
        )

        debit = StructuredDirection(
            account_id=(
                prediction.debit_prediction.account_id
            ),
            direction=(
                prediction.debit_prediction.direction
            ),
            confidence=(
                prediction.debit_prediction.confidence
            ),
            reason=(
                prediction.debit_prediction.reason
                if self.config.include_reasons
                else None
            ),
            requires_review=(
                prediction.debit_prediction.requires_review
            ),
        )

        credit = StructuredDirection(
            account_id=(
                prediction.credit_prediction.account_id
            ),
            direction=(
                prediction.credit_prediction.direction
            ),
            confidence=(
                prediction.credit_prediction.confidence
            ),
            reason=(
                prediction.credit_prediction.reason
                if self.config.include_reasons
                else None
            ),
            requires_review=(
                prediction.credit_prediction.requires_review
            ),
        )

        payment_mode = StructuredPaymentMode(
            mode=prediction.payment_mode.mode,
            confidence=prediction.payment_mode.confidence,
            requires_review=(
                prediction.payment_mode.requires_review
            ),
        )

        confidence = None

        if prediction.confidence is not None:
            confidence = StructuredConfidence(
                overall=prediction.confidence.overall,
                requires_review=(
                    prediction.confidence.requires_review
                ),
                reason=(
                    prediction.confidence.reason
                    if self.config.include_reasons
                    else "Confidence calculated by AI pipeline."
                ),
            )

        semantic_matches = ()

        if self.config.include_semantic_matches:
            semantic_matches = tuple(
                StructuredSemanticMatch(
                    candidate_id=match.candidate_id,
                    candidate_text=match.candidate_text,
                    similarity=match.similarity,
                )
                for match in prediction.semantic_matches
            )

        entities = ()

        if self.config.include_entities:
            entities = tuple(
                prediction.entities
            )

        metadata = {}

        if self.config.include_metadata:
            metadata = dict(
                prediction.metadata
            )

        return StructuredTransaction(
            transaction_id=prediction.transaction_id,
            raw_text=prediction.raw_text,
            normalized_text=prediction.normalized_text,
            amount=prediction.amount,
            transaction_class=prediction.transaction_class,
            classification_confidence=(
                prediction.classification_confidence
            ),
            debit_account=debit_account,
            credit_account=credit_account,
            debit=debit,
            credit=credit,
            payment_mode=payment_mode,
            confidence=confidence,
            entities=entities,
            semantic_matches=semantic_matches,
            metadata=metadata,
            status=prediction.status.value,
        )

    def to_dict(
        self,
        prediction: TransactionPrediction,
    ) -> dict[str, Any]:
        structured = self.serialize(
            prediction
        )

        return self._make_json_safe(
            asdict(structured)
        )

    def to_json(
        self,
        prediction: TransactionPrediction,
    ) -> str:
        import json

        return json.dumps(
            self.to_dict(prediction),
            ensure_ascii=False,
            sort_keys=True,
        )

    @staticmethod
    def _make_json_safe(
        value: Any,
    ) -> Any:
        if isinstance(value, Enum):
            return value.value

        if isinstance(value, dict):
            return {
                str(key): (
                    StructuredOutputSerializer
                    ._make_json_safe(item)
                )
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                StructuredOutputSerializer
                ._make_json_safe(item)
                for item in value
            ]

        if hasattr(value, "item"):
            try:
                return value.item()
            except (ValueError, TypeError):
                pass

        return value
