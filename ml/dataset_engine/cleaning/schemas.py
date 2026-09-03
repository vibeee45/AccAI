from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CleaningConfig:
    required_columns: tuple[str, ...] = (
        "date",
        "transaction",
        "amount",
    )

    normalized_columns: tuple[str, ...] = (
        "date",
        "transaction",
        "amount",
    )

    drop_duplicates: bool = True
    drop_empty_transactions: bool = True
    drop_invalid_dates: bool = True
    drop_invalid_amounts: bool = True

    normalize_text: bool = True
    strip_whitespace: bool = True

    allow_zero_amount: bool = True
    allow_negative_amount: bool = True


@dataclass(frozen=True)
class CleaningStats:
    rows_input: int
    rows_output: int
    rows_removed: int

    duplicate_rows_removed: int
    empty_transaction_rows_removed: int
    invalid_date_rows_removed: int
    invalid_amount_rows_removed: int

    @property
    def rows_rejected(self) -> int:
        return self.rows_removed

    @property
    def retention_rate(self) -> float:
        if self.rows_input == 0:
            return 0.0

        return self.rows_output / self.rows_input
