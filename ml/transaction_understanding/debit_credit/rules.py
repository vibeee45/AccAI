from __future__ import annotations

from dataclasses import dataclass

from .schemas import DebitCredit


@dataclass(frozen=True)
class AccountDirectionRule:
    account_id: str
    direction: DebitCredit
    reason: str


NORMAL_BALANCES: dict[str, DebitCredit] = {
    "cash": DebitCredit.DEBIT,
    "bank": DebitCredit.DEBIT,
    "accounts_receivable": DebitCredit.DEBIT,
    "inventory": DebitCredit.DEBIT,
    "furniture": DebitCredit.DEBIT,
    "machinery": DebitCredit.DEBIT,
    "office_equipment": DebitCredit.DEBIT,
    "computer_equipment": DebitCredit.DEBIT,

    "accounts_payable": DebitCredit.CREDIT,
    "loan": DebitCredit.CREDIT,
    "capital": DebitCredit.CREDIT,

    "sales": DebitCredit.CREDIT,
    "commission_income": DebitCredit.CREDIT,
    "interest_income": DebitCredit.CREDIT,
    "miscellaneous_income": DebitCredit.CREDIT,

    "purchases": DebitCredit.DEBIT,
    "rent_expense": DebitCredit.DEBIT,
    "salary_expense": DebitCredit.DEBIT,
    "utilities_expense": DebitCredit.DEBIT,
    "transport_expense": DebitCredit.DEBIT,
    "advertising_expense": DebitCredit.DEBIT,
    "commission_expense": DebitCredit.DEBIT,
    "interest_expense": DebitCredit.DEBIT,
    "tax_expense": DebitCredit.DEBIT,
    "insurance_expense": DebitCredit.DEBIT,
    "miscellaneous_expense": DebitCredit.DEBIT,
}


ACCOUNT_REASONS: dict[str, str] = {
    "cash": "Cash is an asset account and normally has a debit balance.",
    "bank": "Bank is an asset account and normally has a debit balance.",
    "accounts_receivable": (
        "Accounts receivable is an asset account and normally "
        "has a debit balance."
    ),
    "inventory": (
        "Inventory is an asset account and normally has a debit balance."
    ),
    "furniture": (
        "Furniture is an asset account and normally has a debit balance."
    ),
    "machinery": (
        "Machinery is an asset account and normally has a debit balance."
    ),
    "office_equipment": (
        "Office equipment is an asset account and normally "
        "has a debit balance."
    ),
    "computer_equipment": (
        "Computer equipment is an asset account and normally "
        "has a debit balance."
    ),

    "accounts_payable": (
        "Accounts payable is a liability account and normally "
        "has a credit balance."
    ),
    "loan": (
        "Loan is a liability account and normally has a credit balance."
    ),
    "capital": (
        "Capital is an owner's equity account and normally "
        "has a credit balance."
    ),

    "sales": (
        "Sales is an income account and normally has a credit balance."
    ),
    "commission_income": (
        "Commission income is an income account and normally "
        "has a credit balance."
    ),
    "interest_income": (
        "Interest income is an income account and normally "
        "has a credit balance."
    ),
    "miscellaneous_income": (
        "Miscellaneous income is an income account and normally "
        "has a credit balance."
    ),

    "purchases": (
        "Purchases is a trading account and normally has a debit balance."
    ),
    "rent_expense": (
        "Rent expense is an expense account and normally "
        "has a debit balance."
    ),
    "salary_expense": (
        "Salary expense is an expense account and normally "
        "has a debit balance."
    ),
    "utilities_expense": (
        "Utilities expense is an expense account and normally "
        "has a debit balance."
    ),
    "transport_expense": (
        "Transport expense is an expense account and normally "
        "has a debit balance."
    ),
    "advertising_expense": (
        "Advertising expense is an expense account and normally "
        "has a debit balance."
    ),
    "commission_expense": (
        "Commission expense is an expense account and normally "
        "has a debit balance."
    ),
    "interest_expense": (
        "Interest expense is an expense account and normally "
        "has a debit balance."
    ),
    "tax_expense": (
        "Tax expense is an expense account and normally "
        "has a debit balance."
    ),
    "insurance_expense": (
        "Insurance expense is an expense account and normally "
        "has a debit balance."
    ),
    "miscellaneous_expense": (
        "Miscellaneous expense is an expense account and normally "
        "has a debit balance."
    ),
}


TRANSACTION_DIRECTIONS: dict[str, dict[str, DebitCredit]] = {
    "sales": {
        "sales": DebitCredit.CREDIT,
        "cash": DebitCredit.DEBIT,
        "bank": DebitCredit.DEBIT,
        "accounts_receivable": DebitCredit.DEBIT,
    },
    "purchase": {
        "purchases": DebitCredit.DEBIT,
        "inventory": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
        "accounts_payable": DebitCredit.CREDIT,
    },
    "rent": {
        "rent_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
        "accounts_payable": DebitCredit.CREDIT,
    },
    "salary": {
        "salary_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
        "accounts_payable": DebitCredit.CREDIT,
    },
    "utilities": {
        "utilities_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
        "accounts_payable": DebitCredit.CREDIT,
    },
    "transport": {
        "transport_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
    },
    "advertising": {
        "advertising_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
    },
    "capital_introduction": {
        "cash": DebitCredit.DEBIT,
        "bank": DebitCredit.DEBIT,
        "capital": DebitCredit.CREDIT,
    },
    "loan": {
        "cash": DebitCredit.DEBIT,
        "bank": DebitCredit.DEBIT,
        "loan": DebitCredit.CREDIT,
    },
    "cash_deposit": {
        "bank": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
    },
    "cash_withdrawal": {
        "cash": DebitCredit.DEBIT,
        "bank": DebitCredit.CREDIT,
    },
    "asset_purchase": {
        "furniture": DebitCredit.DEBIT,
        "machinery": DebitCredit.DEBIT,
        "office_equipment": DebitCredit.DEBIT,
        "computer_equipment": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
        "accounts_payable": DebitCredit.CREDIT,
    },
    "asset_sale": {
        "cash": DebitCredit.DEBIT,
        "bank": DebitCredit.DEBIT,
        "accounts_receivable": DebitCredit.DEBIT,
        "furniture": DebitCredit.CREDIT,
        "machinery": DebitCredit.CREDIT,
        "office_equipment": DebitCredit.CREDIT,
        "computer_equipment": DebitCredit.CREDIT,
    },
    "tax": {
        "tax_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
    },
    "insurance": {
        "insurance_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
    },
    "miscellaneous_income": {
        "miscellaneous_income": DebitCredit.CREDIT,
        "cash": DebitCredit.DEBIT,
        "bank": DebitCredit.DEBIT,
        "accounts_receivable": DebitCredit.DEBIT,
    },
    "miscellaneous_expense": {
        "miscellaneous_expense": DebitCredit.DEBIT,
        "cash": DebitCredit.CREDIT,
        "bank": DebitCredit.CREDIT,
        "accounts_payable": DebitCredit.CREDIT,
    },
}


def get_normal_balance(
    account_id: str,
) -> DebitCredit | None:
    return NORMAL_BALANCES.get(
        account_id.strip().lower()
    )


def has_explicit_rule(
    account_id: str,
) -> bool:
    return (
        account_id.strip().lower()
        in NORMAL_BALANCES
    )


def get_reason(
    account_id: str,
) -> str:
    account_id = account_id.strip().lower()

    if account_id in ACCOUNT_REASONS:
        return ACCOUNT_REASONS[account_id]

    return "No explicit accounting rule found."


def get_transaction_direction(
    transaction_class: str,
    account_id: str,
) -> DebitCredit | None:
    transaction_class = transaction_class.strip().lower()
    account_id = account_id.strip().lower()

    return TRANSACTION_DIRECTIONS.get(
        transaction_class,
        {},
    ).get(account_id)


def accounts_can_form_pair(
    transaction_class: str,
    debit_account_id: str,
    credit_account_id: str,
) -> bool:
    debit_account_id = debit_account_id.strip().lower()
    credit_account_id = credit_account_id.strip().lower()

    if debit_account_id == credit_account_id:
        return False

    debit_direction = get_transaction_direction(
        transaction_class,
        debit_account_id,
    )

    credit_direction = get_transaction_direction(
        transaction_class,
        credit_account_id,
    )

    return (
        debit_direction == DebitCredit.DEBIT
        and credit_direction == DebitCredit.CREDIT
    )


# Compatibility exports expected by the package API.
NORMAL_BALANCE_RULES = NORMAL_BALANCES
TRANSACTION_SIDE_RULES = TRANSACTION_DIRECTIONS


def get_direction(
    account_id: str,
) -> DebitCredit:
    direction = get_normal_balance(account_id)

    if direction is None:
        return DebitCredit.DEBIT

    return direction


def has_rule(
    account_id: str,
) -> bool:
    return has_explicit_rule(account_id)

