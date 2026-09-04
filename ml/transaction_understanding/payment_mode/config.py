from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentModeConfig:
    """
    Configuration for payment-mode detection.
    """

    confidence_threshold: float = 0.80

    rule_confidence: float = 0.98

    fallback_confidence: float = 0.50

    def __post_init__(self) -> None:
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError(
                "confidence_threshold must be between 0 and 1."
            )

        if not 0 <= self.rule_confidence <= 1:
            raise ValueError(
                "rule_confidence must be between 0 and 1."
            )

        if not 0 <= self.fallback_confidence <= 1:
            raise ValueError(
                "fallback_confidence must be between 0 and 1."
            )
