from __future__ import annotations

from ml.transaction_understanding.structured_output import (
    StructuredTransaction,
)

from .config import AccountingAdapterConfig
from .schemas import (
    AccountingAccount,
    AccountingAdapterResult,
    AccountingTransaction,
)


class AIToAccountingAdapter:
    def __init__(
        self,
        config: AccountingAdapterConfig | None = None,
    ) -> None:
        self.config = (
            config
            or AccountingAdapterConfig()
        )

    def adapt(
        self,
        transaction: StructuredTransaction,
    ) -> AccountingAdapterResult:
        if not isinstance(
            transaction,
            StructuredTransaction,
        ):
            raise TypeError(
                "transaction must be StructuredTransaction."
            )

        errors: list[str] = []
        warnings: list[str] = []

        if self.config.require_amount:
            if transaction.amount is None:
                errors.append(
                    "Transaction amount is missing."
                )
            elif transaction.amount <= 0:
                errors.append(
                    "Transaction amount must be greater than zero."
                )

        if self.config.require_valid_accounts:
            if not transaction.debit_account.account_id.strip():
                errors.append(
                    "Debit account is missing."
                )

            if not transaction.credit_account.account_id.strip():
                errors.append(
                    "Credit account is missing."
                )

            if (
                transaction.debit_account.account_id
                == transaction.credit_account.account_id
            ):
                errors.append(
                    "Debit and credit accounts "
                    "cannot be the same."
                )

        if self.config.require_valid_directions:
            if transaction.debit.direction != "debit":
                errors.append(
                    "Debit prediction does not have "
                    "debit direction."
                )

            if transaction.credit.direction != "credit":
                errors.append(
                    "Credit prediction does not have "
                    "credit direction."
                )

        confidence = (
            transaction.confidence.overall
            if transaction.confidence is not None
            else transaction.classification_confidence
        )

        if self.config.require_confidence:
            if confidence < self.config.minimum_confidence:
                warnings.append(
                    "AI confidence is below the "
                    "accounting adapter threshold."
                )

        if transaction.status != "success":
            errors.append(
                f"Prediction status is "
                f"'{transaction.status}'."
            )

        if errors:
            return AccountingAdapterResult(
                success=False,
                transaction=None,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

        if confidence < self.config.minimum_confidence:
            warnings.append(
                "Transaction should be reviewed "
                "before accounting posting."
            )

        debit_account = AccountingAccount(
            account_id=(
                transaction.debit_account.account_id
            ),
            account_name=(
                transaction.debit_account.account_name
            ),
        )

        credit_account = AccountingAccount(
            account_id=(
                transaction.credit_account.account_id
            ),
            account_name=(
                transaction.credit_account.account_name
            ),
        )

        accounting_transaction = AccountingTransaction(
            transaction_id=transaction.transaction_id,
            description=transaction.raw_text,
            amount=transaction.amount,
            debit_account=debit_account,
            credit_account=credit_account,
            transaction_class=(
                transaction.transaction_class
            ),
            payment_mode=(
                transaction.payment_mode.mode
            ),
            ai_confidence=confidence,
            requires_review=(
                transaction.status
                == "review_required"
                or confidence
                < self.config.minimum_confidence
            ),
            source_text=transaction.raw_text,
            normalized_text=transaction.normalized_text,
            metadata=dict(
                transaction.metadata
            ),
        )

        return AccountingAdapterResult(
            success=True,
            transaction=accounting_transaction,
            errors=(),
            warnings=tuple(warnings),
        )

    def adapt_many(
        self,
        transactions: list[
            StructuredTransaction
        ]
        | tuple[StructuredTransaction, ...],
    ) -> tuple[AccountingAdapterResult, ...]:
        return tuple(
            self.adapt(transaction)
            for transaction in transactions
        )
