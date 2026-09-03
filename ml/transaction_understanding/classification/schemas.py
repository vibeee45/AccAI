from dataclasses import dataclass
from enum import Enum


class TransactionClass(str, Enum):
    SALES = "sales"
    PURCHASE = "purchase"
    RENT = "rent"
    SALARY = "salary"
    UTILITIES = "utilities"
    TRANSPORT = "transport"
    ADVERTISING = "advertising"
    COMMISSION = "commission"
    INTEREST = "interest"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    BANK_TRANSFER = "bank_transfer"
    CAPITAL_INTRODUCTION = "capital_introduction"
    LOAN = "loan"
    ASSET_PURCHASE = "asset_purchase"
    ASSET_SALE = "asset_sale"
    TAX = "tax"
    INSURANCE = "insurance"
    MISCELLANEOUS_INCOME = "miscellaneous_income"
    MISCELLANEOUS_EXPENSE = "miscellaneous_expense"


@dataclass(frozen=True)
class ClassificationRecord:
    text: str
    label: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")

        if not self.text.strip():
            raise ValueError("text cannot be empty.")

        if not isinstance(self.label, str):
            raise TypeError("label must be a string.")

        if not self.label.strip():
            raise ValueError("label cannot be empty.")


@dataclass(frozen=True)
class ClassificationPrediction:
    label: str
    confidence: float
    probabilities: dict[str, float]
    requires_review: bool

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not self.label:
            raise ValueError("label cannot be empty.")

        if not self.probabilities:
            raise ValueError(
                "probabilities cannot be empty."
            )


@dataclass(frozen=True)
class ClassificationMetrics:
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    sample_count: int

    def __post_init__(self) -> None:
        for value in (
            self.accuracy,
            self.precision_macro,
            self.recall_macro,
            self.f1_macro,
        ):
            if not 0 <= value <= 1:
                raise ValueError(
                    "Classification metrics must be between 0 and 1."
                )

        if self.sample_count < 0:
            raise ValueError(
                "sample_count cannot be negative."
            )
