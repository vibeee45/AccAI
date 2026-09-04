from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceRoutingConfig:
    auto_process_threshold: float = 0.80
    review_threshold: float = 0.50

    def __post_init__(self) -> None:
        if not 0.0 <= self.auto_process_threshold <= 1.0:
            raise ValueError(
                "auto_process_threshold must be between 0 and 1."
            )

        if not 0.0 <= self.review_threshold <= 1.0:
            raise ValueError(
                "review_threshold must be between 0 and 1."
            )

        if (
            self.review_threshold
            > self.auto_process_threshold
        ):
            raise ValueError(
                "review_threshold cannot exceed "
                "auto_process_threshold."
            )
