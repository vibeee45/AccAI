from __future__ import annotations

import random

from ..templates import get_template
from .catalog import (
    BANKS,
    CASH_ACCOUNT,
    CAPITAL_ACCOUNT,
    DRAWINGS_ACCOUNT,
    ELECTRICITY_ACCOUNT,
    LOAN_ACCOUNT,
    PURCHASES_ACCOUNT,
    RENT_ACCOUNT,
    SALARY_ACCOUNT,
    SALES_ACCOUNT,
    TRANSPORT_ACCOUNT,
    get_customers,
    get_suppliers,
)
from .schemas import AccountCombination, AccountEntity


def _combination(
    combination_id: str,
    template_id: str,
    debit: AccountEntity,
    credit: AccountEntity,
) -> AccountCombination:
    combination = AccountCombination(
        combination_id=combination_id,
        template_id=template_id,
        debit_account=debit,
        credit_account=credit,
    )
    combination.validate()
    return combination


def get_template_combinations(
    template_id: str,
) -> tuple[AccountCombination, ...]:
    template = get_template(template_id)

    combinations: list[AccountCombination] = []

    if template_id == "cash_sale":

        combinations = [
            _combination(
                f"{template_id}_cash_{index:03d}",
                template_id,
                CASH_ACCOUNT,
                SALES_ACCOUNT,
            )
            for index in range(1, 6)
        ]

    elif template_id == "credit_sale":
        combinations = [
            _combination(
                f"{template_id}_{customer.entity_id}",
                template_id,
                customer,
                SALES_ACCOUNT,
            )
            for customer in get_customers()
        ]

    elif template_id == "cash_purchase":
        combinations = [
            _combination(
                f"{template_id}_cash_{index:03d}",
                template_id,
                PURCHASES_ACCOUNT,
                CASH_ACCOUNT,
            )
            for index in range(1, 6)
        ]

    elif template_id == "credit_purchase":
        combinations = [
            _combination(
                f"{template_id}_{supplier.entity_id}",
                template_id,
                PURCHASES_ACCOUNT,
                supplier,
            )
            for supplier in get_suppliers()
        ]

    elif template_id == "rent_paid":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                RENT_ACCOUNT,
                CASH_ACCOUNT,
            )
        ]

    elif template_id == "salary_paid":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                SALARY_ACCOUNT,
                CASH_ACCOUNT,
            )
        ]

    elif template_id == "electricity_paid":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                ELECTRICITY_ACCOUNT,
                CASH_ACCOUNT,
            )
        ]

    elif template_id == "transport_paid":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                TRANSPORT_ACCOUNT,
                CASH_ACCOUNT,
            )
        ]

    elif template_id == "commission_received":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                CASH_ACCOUNT,
                SALES_ACCOUNT,
            )
        ]

    elif template_id == "interest_received":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                CASH_ACCOUNT,
                SALES_ACCOUNT,
            )
        ]

    elif template_id == "capital_introduced":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                CASH_ACCOUNT,
                CAPITAL_ACCOUNT,
            )
        ]

    elif template_id == "drawings_cash":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                DRAWINGS_ACCOUNT,
                CASH_ACCOUNT,
            )
        ]

    elif template_id == "loan_received":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                CASH_ACCOUNT,
                LOAN_ACCOUNT,
            )
        ]

    elif template_id == "loan_repayment":
        combinations = [
            _combination(
                f"{template_id}_cash",
                template_id,
                LOAN_ACCOUNT,
                CASH_ACCOUNT,
            )
        ]

    elif template_id == "cash_deposited_bank":
        combinations = [
            _combination(
                f"{template_id}_{bank.entity_id}",
                template_id,
                bank,
                CASH_ACCOUNT,
            )
            for bank in BANKS
        ]

    elif template_id == "cash_withdrawn_bank":
        combinations = [
            _combination(
                f"{template_id}_{bank.entity_id}",
                template_id,
                CASH_ACCOUNT,
                bank,
            )
            for bank in BANKS
        ]

    elif template_id == "bad_debt":
        combinations = [
            _combination(
                f"{template_id}_{customer.entity_id}",
                template_id,
                RENT_ACCOUNT,
                customer,
            )
            for customer in get_customers()
        ]

    else:
        raise KeyError(
            f"No account combinations configured for template: {template_id}"
        )

    return tuple(combinations)


def choose_combination(
    template_id: str,
    rng: random.Random | None = None,
) -> AccountCombination:
    combinations = get_template_combinations(template_id)

    if not combinations:
        raise LookupError(
            f"No combinations available for template: {template_id}"
        )

    random_generator = rng or random.Random()

    return random_generator.choice(combinations)
