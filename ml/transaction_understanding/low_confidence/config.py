from dataclasses import dataclass


@dataclass(frozen=True)
class LowConfidenceConfig:
    """
    Configuration for diagnosing prediction confidence.

    The thresholds intentionally align with the existing confidence
    and routing architecture:

    >= high_threshold
        High confidence

    >= review_threshold and < high_threshold
        Review required

    < review_threshold
        Low confidence
    """

    high_threshold: float = 0.80
    review_threshold: float = 0.50

    # A signal at or below this value is considered weak.
    weak_signal_threshold: float = 0.50

    # A signal substantially below the overall confidence can be
    # reported as a contributing weak signal.
    signal_gap_threshold: float = 0.20

    def __post_init__(self) -> None:
        values = (
            self.high_threshold,
            self.review_threshold,
            self.weak_signal_threshold,
            self.signal_gap_threshold,
        )

        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError(
                "All confidence thresholds must be between 0 and 1."
            )

        if self.review_threshold > self.high_threshold:
            raise ValueError(
                "review_threshold cannot exceed high_threshold."
            )
