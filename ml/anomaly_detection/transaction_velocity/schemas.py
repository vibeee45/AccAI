from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VelocityHistoryItem:
    """Historical transaction data used for velocity calculations."""

    transaction_id: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError("transaction_id cannot be empty.")

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "occurred_at must be timezone-aware."
            )


@dataclass(frozen=True)
class TransactionVelocityFeatures:
    """Calculated transaction velocity features."""

    transaction_id: str

    history_count: int

    transactions_last_1h: int
    transactions_last_24h: int
    transactions_last_7d: int

    time_since_previous_seconds: float

    hourly_rate: float
    daily_rate: float
    weekly_rate: float

    unique_active_days: int

    velocity_ratio: float
    velocity_anomaly: bool

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        integer_fields = (
            ("history_count", self.history_count),
            ("transactions_last_1h", self.transactions_last_1h),
            ("transactions_last_24h", self.transactions_last_24h),
            ("transactions_last_7d", self.transactions_last_7d),
            ("unique_active_days", self.unique_active_days),
        )

        for name, value in integer_fields:
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

        numeric_fields = (
            (
                "time_since_previous_seconds",
                self.time_since_previous_seconds,
            ),
            ("hourly_rate", self.hourly_rate),
            ("daily_rate", self.daily_rate),
            ("weekly_rate", self.weekly_rate),
            ("velocity_ratio", self.velocity_ratio),
        )

        for name, value in numeric_fields:
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

        if self.transactions_last_1h > self.transactions_last_24h:
            raise ValueError(
                "transactions_last_1h cannot exceed "
                "transactions_last_24h."
            )

        if self.transactions_last_24h > self.transactions_last_7d:
            raise ValueError(
                "transactions_last_24h cannot exceed "
                "transactions_last_7d."
            )

    @property
    def has_history(self) -> bool:
        """Return whether historical transactions exist."""

        return self.history_count > 0

    @property
    def has_recent_activity(self) -> bool:
        """Return whether any transaction occurred in the last hour."""

        return self.transactions_last_1h > 0

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""

        return {
            "transaction_id": self.transaction_id,
            "history_count": self.history_count,
            "transactions_last_1h": self.transactions_last_1h,
            "transactions_last_24h": self.transactions_last_24h,
            "transactions_last_7d": self.transactions_last_7d,
            "time_since_previous_seconds": (
                self.time_since_previous_seconds
            ),
            "hourly_rate": self.hourly_rate,
            "daily_rate": self.daily_rate,
            "weekly_rate": self.weekly_rate,
            "unique_active_days": self.unique_active_days,
            "velocity_ratio": self.velocity_ratio,
            "velocity_anomaly": self.velocity_anomaly,
        }
