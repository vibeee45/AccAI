from __future__ import annotations

from .config import PaymentModeConfig
from .detector import PaymentModeDetector
from .schemas import PaymentModePrediction


class PaymentModeService:
    """
    Public service interface for payment-mode detection.
    """

    def __init__(
        self,
        config: PaymentModeConfig | None = None,
    ) -> None:
        self.detector = PaymentModeDetector(config)

    def detect(
        self,
        text: str,
    ) -> PaymentModePrediction:
        return self.detector.detect(text)

    def detect_many(
        self,
        texts: list[str],
    ) -> list[PaymentModePrediction]:
        return self.detector.detect_many(texts)

    def is_ready(self) -> bool:
        return self.detector is not None
