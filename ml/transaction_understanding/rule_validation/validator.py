from __future__ import annotations

from decimal import Decimal

from ml.transaction_understanding.accounting_adapter import (
    AccountingTransaction,
)

from .config import RuleValidationConfig
from .schemas import (
    RuleValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationStatus,
)


class AccountingRuleValidator:
    """
    Deterministic validation layer between AI predictions
    and journal generation.

    AI predicts the accounting treatment.
    This validator checks whether that treatment satisfies
    deterministic accounting rules.
    """

    def __init__(
        self,
        config: RuleValidationConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else RuleValidationConfig()
        )

    def validate(
        self,
        transaction: AccountingTransaction,
    ) -> RuleValidationResult:
        if not isinstance(
            transaction,
            AccountingTransaction,
        ):
            raise TypeError(
                "transaction must be AccountingTransaction."
            )

        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        amount = transaction.amount

        if (
            self.config.require_positive_amount
            and amount <= Decimal("0")
        ):
            errors.append(
                ValidationIssue(
                    code="INVALID_AMOUNT",
                    message=(
                        "Transaction amount must be "
                        "greater than zero."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
            )

        debit_account = transaction.debit_account
        credit_account = transaction.credit_account

        if (
            self.config.require_distinct_accounts
            and debit_account.account_id
            == credit_account.account_id
        ):
            errors.append(
                ValidationIssue(
                    code="SAME_ACCOUNTS",
                    message=(
                        "Debit and credit accounts "
                        "cannot be the same."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
            )

        if not debit_account.account_id.strip():
            errors.append(
                ValidationIssue(
                    code="MISSING_DEBIT_ACCOUNT",
                    message="Debit account is missing.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if not credit_account.account_id.strip():
            errors.append(
                ValidationIssue(
                    code="MISSING_CREDIT_ACCOUNT",
                    message="Credit account is missing.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if not transaction.transaction_class.strip():
            errors.append(
                ValidationIssue(
                    code="MISSING_TRANSACTION_CLASS",
                    message=(
                        "Transaction class is missing."
                    ),
                    severity=ValidationSeverity.ERROR,
                )
            )

        if not transaction.payment_mode.strip():
            errors.append(
                ValidationIssue(
                    code="MISSING_PAYMENT_MODE",
                    message="Payment mode is missing.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if transaction.ai_confidence < (
            self.config.confidence_threshold
        ):
            warnings.append(
                ValidationIssue(
                    code="LOW_AI_CONFIDENCE",
                    message=(
                        "AI confidence is below the "
                        "configured validation threshold."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )

        if transaction.requires_review:
            warnings.append(
                ValidationIssue(
                    code="AI_REVIEW_REQUIRED",
                    message=(
                        "The transaction was marked "
                        "for human review."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )

        if errors:
            return RuleValidationResult(
                status=ValidationStatus.INVALID,
                valid=False,
                issues=tuple(errors),
                warnings=tuple(warnings),
                confidence=0.0,
                metadata={
                    "transaction_id": (
                        transaction.transaction_id
                    ),
                },
            )

        if warnings:
            return RuleValidationResult(
                status=ValidationStatus.REVIEW_REQUIRED,
                valid=True,
                issues=(),
                warnings=tuple(warnings),
                confidence=transaction.ai_confidence,
                metadata={
                    "transaction_id": (
                        transaction.transaction_id
                    ),
                },
            )

        return RuleValidationResult(
            status=ValidationStatus.VALID,
            valid=True,
            issues=(),
            warnings=(),
            confidence=transaction.ai_confidence,
            metadata={
                "transaction_id": (
                    transaction.transaction_id
                ),
            },
        )

    def validate_many(
        self,
        transactions: list[AccountingTransaction]
        | tuple[AccountingTransaction, ...],
    ) -> tuple[RuleValidationResult, ...]:
        return tuple(
            self.validate(transaction)
            for transaction in transactions
        )
