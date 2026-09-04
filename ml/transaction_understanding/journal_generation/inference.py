from __future__ import annotations

from ml.transaction_understanding.accounting_adapter import (
    AccountingTransaction,
)

from .config import JournalGenerationConfig
from .generator import JournalGenerator
from .schemas import JournalGenerationResult


class JournalGenerationService:
    """
    Public service interface for journal generation.
    """

    def __init__(
        self,
        config: JournalGenerationConfig | None = None,
    ) -> None:
        self.generator = JournalGenerator(
            config
        )

    def generate(
        self,
        transaction: AccountingTransaction,
    ) -> JournalGenerationResult:
        return self.generator.generate(
            transaction
        )

    def generate_many(
        self,
        transactions: list[AccountingTransaction]
        | tuple[AccountingTransaction, ...],
    ) -> tuple[JournalGenerationResult, ...]:
        return self.generator.generate_many(
            transactions
        )

    def is_ready(self) -> bool:
        return True
