from __future__ import annotations

from typing import Any

from ml.transaction_understanding.prediction import (
    TransactionPrediction,
)

from .config import StructuredOutputConfig
from .schemas import StructuredTransaction
from .serializer import StructuredOutputSerializer


class StructuredOutputService:
    def __init__(
        self,
        config: StructuredOutputConfig | None = None,
    ) -> None:
        self.serializer = StructuredOutputSerializer(
            config
        )

    def serialize(
        self,
        prediction: TransactionPrediction,
    ) -> StructuredTransaction:
        return self.serializer.serialize(
            prediction
        )

    def to_dict(
        self,
        prediction: TransactionPrediction,
    ) -> dict[str, Any]:
        return self.serializer.to_dict(
            prediction
        )

    def to_json(
        self,
        prediction: TransactionPrediction,
    ) -> str:
        return self.serializer.to_json(
            prediction
        )

    def is_ready(self) -> bool:
        return True
