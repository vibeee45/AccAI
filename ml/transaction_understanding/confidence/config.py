from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceConfig:
    classification_weight: float = 0.25
    account_weight: float = 0.25
    debit_credit_weight: float = 0.20
    payment_mode_weight: float = 0.10
    semantic_weight: float = 0.20

    threshold: float = 0.80

    def __post_init__(self) -> None:
        weights = (
            self.classification_weight,
            self.account_weight,
            self.debit_credit_weight,
            self.payment_mode_weight,
            self.semantic_weight,
        )

        if any(weight < 0.0 or weight > 1.0 for weight in weights):
            raise ValueError(
                "All confidence weights must be between 0 and 1."
            )

        total = sum(weights)

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                "Confidence weights must sum to 1.0."
            )

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(
                "threshold must be between 0 and 1."
            )
