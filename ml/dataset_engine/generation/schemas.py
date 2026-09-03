from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class GenerationConfig:
    rows: int = 1000
    seed: int = 42
    start_date: date = date(2026, 1, 1)
    end_date: date = date(2026, 12, 31)
    min_amount: Decimal = Decimal("100")
    max_amount: Decimal = Decimal("100000")
    include_template_id: bool = True

    def validate(self) -> None:
        if self.rows < 0:
            raise ValueError("rows cannot be negative")

        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")

        if self.min_amount <= Decimal("0"):
            raise ValueError("min_amount must be greater than zero")

        if self.max_amount < self.min_amount:
            raise ValueError("max_amount cannot be less than min_amount")


@dataclass(frozen=True)
class GeneratedTransaction:
    transaction_id: str
    date: date
    transaction: str
    amount: Decimal
    template_id: str
    debit_account: str
    credit_account: str
    category: str

    def validate(self) -> None:
        if not self.transaction_id:
            raise ValueError("transaction_id cannot be empty")

        if not self.transaction.strip():
            raise ValueError("transaction cannot be empty")

        if self.amount <= Decimal("0"):
            raise ValueError("amount must be greater than zero")

        if not self.template_id:
            raise ValueError("template_id cannot be empty")

        if not self.debit_account:
            raise ValueError("debit_account cannot be empty")

        if not self.credit_account:
            raise ValueError("credit_account cannot be empty")
