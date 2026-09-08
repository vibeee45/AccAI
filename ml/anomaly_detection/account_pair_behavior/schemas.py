from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AccountPairHistoryItem:
    transaction_id: str
    occurred_at: datetime
    debit_account_id: str
    credit_account_id: str

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError("transaction_id cannot be empty.")

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "occurred_at must be timezone-aware."
            )

        if not self.debit_account_id.strip():
            raise ValueError(
                "debit_account_id cannot be empty."
            )

        if not self.credit_account_id.strip():
            raise ValueError(
                "credit_account_id cannot be empty."
            )

        if self.debit_account_id == self.credit_account_id:
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
class AccountPairBehaviorFeatures:
    transaction_id: str
    account_pair: str
    history_count: int
    pair_frequency: int
    pair_ratio: float
    unique_pair_count: int
    pair_seen_before: bool

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not self.account_pair.strip():
            raise ValueError(
                "account_pair cannot be empty."
            )

        integer_fields = (
            ("history_count", self.history_count),
            ("pair_frequency", self.pair_frequency),
            ("unique_pair_count", self.unique_pair_count),
        )

        for name, value in integer_fields:
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

        if not 0.0 <= self.pair_ratio <= 1.0:
            raise ValueError(
                "pair_ratio must be between 0 and 1."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "account_pair": self.account_pair,
            "history_count": self.history_count,
            "pair_frequency": self.pair_frequency,
            "pair_ratio": self.pair_ratio,
            "unique_pair_count": self.unique_pair_count,
            "pair_seen_before": self.pair_seen_before,
        }
