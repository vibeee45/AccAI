from dataclasses import dataclass
from enum import Enum


class DebitCredit(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True)
class DebitCreditPrediction:
    """
    Predicted accounting direction for an account.
    """

    account_id: str
    account_name: str
    direction: DebitCredit
    confidence: float
    reason: str
    requires_review: bool

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name.strip():
            raise ValueError(
                "account_name cannot be empty."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )


@dataclass(frozen=True)
class DebitCreditPairPrediction:
    """
    Prediction for both sides of a double-entry transaction.
    """

    debit_account_id: str
    debit_account_name: str

    credit_account_id: str
    credit_account_name: str

    confidence: float
    requires_review: bool

    def __post_init__(self) -> None:
        if not self.debit_account_id.strip():
            raise ValueError(
                "debit_account_id cannot be empty."
            )

        if not self.credit_account_id.strip():
            raise ValueError(
                "credit_account_id cannot be empty."
            )

        if (
            self.debit_account_id
            == self.credit_account_id
        ):
            raise ValueError(
                "Debit and credit accounts must be different."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )


@dataclass(frozen=True)
class DebitCreditRule:
    """
    Accounting rule describing the normal direction
    for an account category.
    """

    account_id: str
    direction: DebitCredit
    reason: str

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )
