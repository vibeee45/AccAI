from __future__ import annotations

from ml.transaction_understanding.accounting_adapter import (
    AccountingTransaction,
)

from .config import RuleValidationConfig
from .schemas import RuleValidationResult
from .validator import AccountingRuleValidator


class RuleValidationService:
    """
    Public service interface for deterministic
    accounting rule validation.
    """

    def __init__(
        self,
        config: RuleValidationConfig | None = None,
    ) -> None:
        self.validator = AccountingRuleValidator(
            config
        )

    def validate(
        self,
        transaction: AccountingTransaction,
    ) -> RuleValidationResult:
        return self.validator.validate(
            transaction
        )

    def validate_many(
        self,
        transactions: list[AccountingTransaction]
        | tuple[AccountingTransaction, ...],
    ) -> tuple[RuleValidationResult, ...]:
        return self.validator.validate_many(
            transactions
        )

    def is_ready(self) -> bool:
        return True
