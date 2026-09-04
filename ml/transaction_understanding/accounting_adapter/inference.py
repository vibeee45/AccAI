from __future__ import annotations

from ml.transaction_understanding.structured_output import (
    StructuredTransaction,
)

from .adapter import AIToAccountingAdapter
from .config import AccountingAdapterConfig
from .schemas import AccountingAdapterResult


class AccountingAdapterService:
    def __init__(
        self,
        config: AccountingAdapterConfig | None = None,
    ) -> None:
        self.adapter = AIToAccountingAdapter(
            config
        )

    def adapt(
        self,
        transaction: StructuredTransaction,
    ) -> AccountingAdapterResult:
        return self.adapter.adapt(
            transaction
        )

    def adapt_many(
        self,
        transactions: list[
            StructuredTransaction
        ]
        | tuple[StructuredTransaction, ...],
    ) -> tuple[AccountingAdapterResult, ...]:
        return self.adapter.adapt_many(
            transactions
        )

    def is_ready(self) -> bool:
        return True
