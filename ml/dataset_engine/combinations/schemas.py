from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AccountType(str, Enum):
    CASH = "cash"
    BANK = "bank"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    EXPENSE = "expense"
    INCOME = "income"
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"


@dataclass(frozen=True)
class AccountEntity:
    entity_id: str
    name: str
    account_name: str
    account_type: AccountType

    def validate(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id cannot be empty")

        if not self.name.strip():
            raise ValueError("name cannot be empty")

        if not self.account_name.strip():
            raise ValueError("account_name cannot be empty")


@dataclass(frozen=True)
class AccountCombination:
    combination_id: str
    template_id: str
    debit_account: AccountEntity
    credit_account: AccountEntity

    def validate(self) -> None:
        if not self.combination_id.strip():
            raise ValueError("combination_id cannot be empty")

        if not self.template_id.strip():
            raise ValueError("template_id cannot be empty")

        self.debit_account.validate()
        self.credit_account.validate()

        if (
            self.debit_account.account_name
            == self.credit_account.account_name
        ):
            raise ValueError(
                "debit and credit accounts cannot be identical"
            )
