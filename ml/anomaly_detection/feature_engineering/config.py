from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureEngineeringConfig:
    """Configuration for deterministic anomaly-detection features."""

    log_amount_offset: float = 1.0
    min_text_length: int = 0
    min_word_count: int = 0

    def __post_init__(self) -> None:
        if self.log_amount_offset <= 0:
            raise ValueError(
                "log_amount_offset must be greater than 0."
            )

        if self.min_text_length < 0:
            raise ValueError(
                "min_text_length cannot be negative."
            )

        if self.min_word_count < 0:
            raise ValueError(
                "min_word_count cannot be negative."
            )
