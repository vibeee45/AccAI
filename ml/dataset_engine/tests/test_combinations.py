import random

import pytest

from ml.dataset_engine.combinations import (
    AccountType,
    choose_combination,
    get_account_by_name,
    get_customers,
    get_suppliers,
    get_template_combinations,
)


def test_customers_exist():
    customers = get_customers()

    assert len(customers) >= 5
    assert all(customer.account_type == AccountType.CUSTOMER for customer in customers)


def test_suppliers_exist():
    suppliers = get_suppliers()

    assert len(suppliers) >= 5
    assert all(supplier.account_type == AccountType.SUPPLIER for supplier in suppliers)


@pytest.mark.parametrize(
    "template_id",
    [
        "cash_sale",
        "credit_sale",
        "cash_purchase",
        "credit_purchase",
        "rent_paid",
        "salary_paid",
        "electricity_paid",
        "transport_paid",
        "commission_received",
        "interest_received",
        "capital_introduced",
        "drawings_cash",
        "loan_received",
        "loan_repayment",
        "cash_deposited_bank",
        "cash_withdrawn_bank",
        "bad_debt",
    ],
)
def test_every_template_has_combinations(template_id):
    combinations = get_template_combinations(template_id)

    assert combinations

    for combination in combinations:
        combination.validate()
        assert combination.template_id == template_id


def test_credit_sales_use_customers():
    combinations = get_template_combinations("credit_sale")

    assert len(combinations) == len(get_customers())

    assert all(
        combination.debit_account.account_type == AccountType.CUSTOMER
        for combination in combinations
    )


def test_credit_purchases_use_suppliers():
    combinations = get_template_combinations("credit_purchase")

    assert len(combinations) == len(get_suppliers())

    assert all(
        combination.credit_account.account_type == AccountType.SUPPLIER
        for combination in combinations
    )


def test_combination_ids_are_unique():
    combinations = get_template_combinations("credit_sale")

    ids = [combination.combination_id for combination in combinations]

    assert len(ids) == len(set(ids))


def test_choose_combination_is_deterministic_with_seed():
    first = choose_combination(
        "credit_sale",
        random.Random(42),
    )

    second = choose_combination(
        "credit_sale",
        random.Random(42),
    )

    assert first == second


def test_choose_combination_returns_valid_combination():
    combination = choose_combination(
        "credit_purchase",
        random.Random(10),
    )

    assert combination.template_id == "credit_purchase"
    combination.validate()


def test_unknown_template_raises():
    with pytest.raises(KeyError):
        get_template_combinations("unknown_template")


def test_unknown_account_raises():
    with pytest.raises(KeyError):
        get_account_by_name("Unknown Account")


def test_account_lookup():
    account = get_account_by_name("Cash")

    assert account.account_name == "Cash"
    assert account.account_type == AccountType.CASH


def test_customer_lookup_by_shared_account_name():
    account = get_account_by_name("Accounts Receivable")

    assert account.account_type == AccountType.CUSTOMER


def test_supplier_combination_accounts():
    combinations = get_template_combinations("credit_purchase")

    for combination in combinations:
        assert combination.debit_account.account_name == "Purchases"
        assert combination.credit_account.account_name == "Accounts Payable"


def test_customer_combination_accounts():
    combinations = get_template_combinations("credit_sale")

    for combination in combinations:
        assert combination.debit_account.account_name == "Accounts Receivable"
        assert combination.credit_account.account_name == "Sales"


def test_no_same_debit_credit_account():
    for template_id in [
        "cash_sale",
        "credit_sale",
        "cash_purchase",
        "credit_purchase",
        "rent_paid",
        "salary_paid",
        "electricity_paid",
        "transport_paid",
        "commission_received",
        "interest_received",
        "capital_introduced",
        "drawings_cash",
        "loan_received",
        "loan_repayment",
        "cash_deposited_bank",
        "cash_withdrawn_bank",
        "bad_debt",
    ]:
        combinations = get_template_combinations(template_id)

        for combination in combinations:
            assert (
                combination.debit_account.account_name
                != combination.credit_account.account_name
            )
