from __future__ import annotations

from .config import PaymentModeConfig
from .rules import detect_payment_modes
from .schemas import PaymentMode, PaymentModePrediction


class PaymentModeDetector:
    """
    Detect payment mode from transaction text.

    Explicit payment-mode terminology receives high confidence.
    Ambiguous transactions fall back to UNKNOWN and require review.
    """

    def __init__(
        self,
        config: PaymentModeConfig | None = None,
    ) -> None:
        self.config = config or PaymentModeConfig()

    def detect(
        self,
        text: str,
    ) -> PaymentModePrediction:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")

        if not text.strip():
            raise ValueError("text cannot be empty.")

        matches = detect_payment_modes(text)

        # No explicit payment mode.
        if not matches:
            confidence = self.config.fallback_confidence

            return PaymentModePrediction(
                payment_mode=PaymentMode.UNKNOWN,
                confidence=confidence,
                requires_review=True,
                reason=(
                    "No explicit payment mode was detected. "
                    "Human review is required."
                ),
            )

        # Multiple conflicting payment modes.
        if len(matches) > 1:
            return PaymentModePrediction(
                payment_mode=PaymentMode.UNKNOWN,
                confidence=self.config.fallback_confidence,
                requires_review=True,
                reason=(
                    "Multiple payment modes were detected, so "
                    "the payment mode requires human review."
                ),
            )

        payment_mode = matches[0]
        confidence = self.config.rule_confidence

        return PaymentModePrediction(
            payment_mode=payment_mode,
            confidence=confidence,
            requires_review=(
                confidence < self.config.confidence_threshold
            ),
            reason=(
                f"Payment mode '{payment_mode.value}' was explicitly "
                "identified from the transaction text."
            ),
        )

    def detect_many(
        self,
        texts: list[str],
    ) -> list[PaymentModePrediction]:
        if not texts:
            raise ValueError("texts cannot be empty.")

        return [
            self.detect(text)
            for text in texts
        ]
