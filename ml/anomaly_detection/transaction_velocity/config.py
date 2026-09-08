from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransactionVelocityConfig:
    """Configuration for transaction velocity feature engineering."""

    short_window_seconds: int = 60 * 60
    daily_window_seconds: int = 24 * 60 * 60
    weekly_window_seconds: int = 7 * 24 * 60 * 60
    max_history: int | None = None

    def __post_init__(self) -> None:
        if self.short_window_seconds <= 0:
            raise ValueError(
                "short_window_seconds must be positive."
            )

        if self.daily_window_seconds <= 0:
            raise ValueError(
                "daily_window_seconds must be positive."
            )

        if self.weekly_window_seconds <= 0:
            raise ValueError(
                "weekly_window_seconds must be positive."
            )

        if self.short_window_seconds > self.daily_window_seconds:
            raise ValueError(
                "short_window_seconds cannot exceed daily_window_seconds."
            )

        if self.daily_window_seconds > self.weekly_window_seconds:
            raise ValueError(
                "daily_window_seconds cannot exceed weekly_window_seconds."
            )

        if self.max_history is not None and self.max_history <= 0:
            raise ValueError(
                "max_history must be positive."
            )
