from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class TemplateCategory(str, Enum):
    SALES = "sales"
    PURCHASES = "purchases"
    EXPENSES = "expenses"
    INCOME = "income"
    CAPITAL = "capital"
    DRAWINGS = "drawings"
    LOANS = "loans"
    BANKING = "banking"
    ADJUSTMENTS = "adjustments"


@dataclass(frozen=True)
class AccountRole:
    name: str
    description: str


@dataclass(frozen=True)
class AccountingTemplate:
    template_id: str
    name: str
    category: TemplateCategory
    description: str
    debit_account: str
    credit_account: str
    amount_required: bool = True
    supports_cash: bool = True
    supports_credit: bool = False

    def validate_amount(self, amount: Decimal) -> bool:
        return amount > Decimal("0")

    def accounts(self) -> tuple[str, str]:
        return self.debit_account, self.credit_account


@dataclass(frozen=True)
class TemplateMatch:
    template_id: str
    confidence: Decimal
    matched_keywords: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return (
            Decimal("0") <= self.confidence <= Decimal("1")
            and bool(self.template_id)
        )
