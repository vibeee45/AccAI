from __future__ import annotations

from decimal import Decimal

from ml.transaction_understanding.accounting_adapter import (
    AccountingTransaction,
)

from .config import JournalGenerationConfig
from .schemas import (
    JournalEntry,
    JournalGenerationResult,
    JournalLine,
)


class JournalGenerator:
    """
    Converts an AccountingTransaction into a
    deterministic double-entry JournalEntry.

    This layer does not decide whether the accounts
    are economically correct. That responsibility
    belongs to Phase 5.5 Rule Validation.
    """

    def __init__(
        self,
        config: JournalGenerationConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else JournalGenerationConfig()
        )

    @staticmethod
    def _to_decimal(value: object) -> Decimal:
        if isinstance(value, Decimal):
            return value

        if isinstance(value, int):
            return Decimal(value)

        if isinstance(value, float):
            return Decimal(str(value))

        if isinstance(value, str):
            return Decimal(value.strip())

        raise TypeError(
            "Amount must be Decimal, int, float, or str."
        )

    def generate(
        self,
        transaction: AccountingTransaction,
    ) -> JournalGenerationResult:
        if not isinstance(
            transaction,
            AccountingTransaction,
        ):
            raise TypeError(
                "transaction must be "
                "AccountingTransaction."
            )

        errors: list[str] = []
        warnings: list[str] = []

        try:
            amount = self._to_decimal(
                transaction.amount
            )
        except (TypeError, ValueError) as exc:
            return JournalGenerationResult(
                success=False,
                journal=None,
                errors=(
                    f"Invalid transaction amount: {exc}",
                ),
            )

        if (
            self.config.require_positive_amount
            and amount <= Decimal("0")
        ):
            errors.append(
                "Transaction amount must be "
                "greater than zero."
            )

        debit_account = transaction.debit_account
        credit_account = transaction.credit_account

        if (
            self.config.require_distinct_accounts
            and debit_account.account_id
            == credit_account.account_id
        ):
            errors.append(
                "Debit and credit accounts "
                "cannot be the same."
            )

        if errors:
            return JournalGenerationResult(
                success=False,
                journal=None,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

        narration = (
            transaction.description
            if self.config.generate_narration
            else (
                f"{transaction.transaction_class} "
                "transaction"
            )
        )

        debit_line = JournalLine(
            account_id=debit_account.account_id,
            account_name=debit_account.account_name,
            description=narration,
            debit=amount,
            credit=Decimal("0"),
        )

        credit_line = JournalLine(
            account_id=credit_account.account_id,
            account_name=credit_account.account_name,
            description=narration,
            debit=Decimal("0"),
            credit=amount,
        )

        journal = JournalEntry(
            journal_id=(
                f"JE-{transaction.transaction_id}"
            ),
            transaction_id=transaction.transaction_id,
            narration=narration,
            amount=amount,
            lines=(
                debit_line,
                credit_line,
            ),
            transaction_class=(
                transaction.transaction_class
            ),
            payment_mode=transaction.payment_mode,
            ai_confidence=(
                transaction.ai_confidence
            ),
            requires_review=(
                transaction.requires_review
            ),
            metadata=dict(
                transaction.metadata
            ),
        )

        return JournalGenerationResult(
            success=True,
            journal=journal,
            errors=(),
            warnings=tuple(warnings),
        )

    def generate_many(
        self,
        transactions: list[AccountingTransaction]
        | tuple[AccountingTransaction, ...],
    ) -> tuple[JournalGenerationResult, ...]:
        return tuple(
            self.generate(transaction)
            for transaction in transactions
        )
