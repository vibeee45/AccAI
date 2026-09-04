from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AccountingAccount:
    account_id: str
    account_name: str

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name.strip():
            raise ValueError(
                "account_name cannot be empty."
            )


@dataclass(frozen=True)
class AccountingTransaction:
    transaction_id: str
    description: str
    amount: float

    debit_account: AccountingAccount
    credit_account: AccountingAccount

    transaction_class: str
    payment_mode: str

    ai_confidence: float
    requires_review: bool

    source_text: str
    normalized_text: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not self.description.strip():
            raise ValueError(
                "description cannot be empty."
            )

        if self.amount <= 0:
            raise ValueError(
                "amount must be greater than zero."
            )

        if not isinstance(
            self.debit_account,
            AccountingAccount,
        ):
            raise TypeError(
                "debit_account must be AccountingAccount."
            )

        if not isinstance(
            self.credit_account,
            AccountingAccount,
        ):
            raise TypeError(
                "credit_account must be AccountingAccount."
            )

        if (
            self.debit_account.account_id
            == self.credit_account.account_id
        ):
            raise ValueError(
                "debit and credit accounts "
                "cannot be the same."
            )

        if not self.transaction_class.strip():
            raise ValueError(
                "transaction_class cannot be empty."
            )

        if not self.payment_mode.strip():
            raise ValueError(
                "payment_mode cannot be empty."
            )

        if not 0.0 <= self.ai_confidence <= 1.0:
            raise ValueError(
                "ai_confidence must be between 0 and 1."
            )

        if not self.source_text.strip():
            raise ValueError(
                "source_text cannot be empty."
            )

        if not self.normalized_text.strip():
            raise ValueError(
                "normalized_text cannot be empty."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )


@dataclass(frozen=True)
class AccountingAdapterResult:
    success: bool
    transaction: AccountingTransaction | None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.success and self.transaction is None:
            raise ValueError(
                "Successful result must contain "
                "an accounting transaction."
            )

        if not self.success and self.transaction is not None:
            raise ValueError(
                "Failed result cannot contain "
                "an accounting transaction."
            )

        if not isinstance(
            self.errors,
            tuple,
        ):
            raise TypeError(
                "errors must be a tuple."
            )

        if not isinstance(
            self.warnings,
            tuple,
        ):
            raise TypeError(
                "warnings must be a tuple."
            )
