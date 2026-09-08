from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class HistoricalTransaction:
    transaction_id: str
    occurred_at: datetime
    amount: float
    transaction_class: str
    payment_mode: str
    debit_account_id: str
    credit_account_id: str

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "occurred_at must be timezone-aware."
            )

        if self.amount < 0:
            raise ValueError(
                "amount cannot be negative."
            )

        if not self.transaction_class.strip():
            raise ValueError(
                "transaction_class cannot be empty."
            )

        if not self.payment_mode.strip():
            raise ValueError(
                "payment_mode cannot be empty."
            )

        if not self.debit_account_id.strip():
            raise ValueError(
                "debit_account_id cannot be empty."
            )

        if not self.credit_account_id.strip():
            raise ValueError(
                "credit_account_id cannot be empty."
            )

        if (
            self.debit_account_id
            == self.credit_account_id
        ):
            raise ValueError(
                "debit and credit accounts cannot be the same."
            )

    @property
    def account_pair(self) -> str:
        return (
            f"{self.debit_account_id}"
            f"->{self.credit_account_id}"
        )


@dataclass(frozen=True)
class HistoricalBehaviorFeatures:
    transaction_id: str
    history_count: int

    amount_mean: float
    amount_std: float
    amount_min: float
    amount_max: float

    amount_deviation_from_mean: float
    amount_z_score: float

    class_frequency: int
    account_pair_frequency: int
    payment_mode_frequency: int

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        integer_fields = (
            ("history_count", self.history_count),
            ("class_frequency", self.class_frequency),
            (
                "account_pair_frequency",
                self.account_pair_frequency,
            ),
            (
                "payment_mode_frequency",
                self.payment_mode_frequency,
            ),
        )

        for name, value in integer_fields:
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

        numeric_fields = (
            ("amount_mean", self.amount_mean),
            ("amount_std", self.amount_std),
            ("amount_min", self.amount_min),
            ("amount_max", self.amount_max),
            (
                "amount_deviation_from_mean",
                self.amount_deviation_from_mean,
            ),
            ("amount_z_score", self.amount_z_score),
        )

        for name, value in numeric_fields:
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

    @property
    def has_history(self) -> bool:
        return self.history_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "history_count": self.history_count,
            "amount_mean": self.amount_mean,
            "amount_std": self.amount_std,
            "amount_min": self.amount_min,
            "amount_max": self.amount_max,
            "amount_deviation_from_mean": (
                self.amount_deviation_from_mean
            ),
            "amount_z_score": self.amount_z_score,
            "class_frequency": self.class_frequency,
            "account_pair_frequency": (
                self.account_pair_frequency
            ),
            "payment_mode_frequency": (
                self.payment_mode_frequency
            ),
        }
