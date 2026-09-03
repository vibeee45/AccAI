from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class VariationConfig:
    variations_per_transaction: int = 5
    seed: int = 42
    include_amount: bool = True

    def validate(self) -> None:
        if self.variations_per_transaction < 1:
            raise ValueError(
                "variations_per_transaction must be at least 1"
            )


@dataclass(frozen=True)
class TransactionVariation:
    variation_id: str
    template_id: str
    transaction: str
    amount: Decimal
    debit_account: str
    credit_account: str
    category: str
    source_transaction_id: str | None = None

    def validate(self) -> None:
        if not self.variation_id.strip():
            raise ValueError("variation_id cannot be empty")

        if not self.template_id.strip():
            raise ValueError("template_id cannot be empty")

        if not self.transaction.strip():
            raise ValueError("transaction cannot be empty")

        if self.amount <= Decimal("0"):
            raise ValueError("amount must be greater than zero")

        if not self.debit_account.strip():
            raise ValueError("debit_account cannot be empty")

        if not self.credit_account.strip():
            raise ValueError("credit_account cannot be empty")

        if not self.category.strip():
            raise ValueError("category cannot be empty")
