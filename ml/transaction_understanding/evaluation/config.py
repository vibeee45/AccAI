from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationConfig:
    zero_division: int = 0
    confidence_bins: int = 10

    def __post_init__(self) -> None:
        if self.zero_division not in (0, 1):
            raise ValueError(
                "zero_division must be either 0 or 1."
            )

        if self.confidence_bins <= 0:
            raise ValueError(
                "confidence_bins must be greater than zero."
            )
