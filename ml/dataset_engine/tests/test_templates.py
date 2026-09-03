from decimal import Decimal

import pytest

from ml.dataset_engine.templates import (
    TemplateCategory,
    extract_amount,
    get_all_templates,
    get_template,
    get_templates_by_category,
    match_template,
    resolve_template,
)


def test_template_catalog_is_not_empty():
    assert len(get_all_templates()) >= 10


def test_template_ids_are_unique():
    templates = get_all_templates()
    ids = [template.template_id for template in templates]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(
    "template_id,debit,credit",
    [
        ("cash_sale", "Cash", "Sales"),
        ("credit_sale", "Accounts Receivable", "Sales"),
        ("cash_purchase", "Purchases", "Cash"),
        ("credit_purchase", "Purchases", "Accounts Payable"),
        ("rent_paid", "Rent Expense", "Cash"),
        ("salary_paid", "Salary Expense", "Cash"),
        ("capital_introduced", "Cash", "Capital"),
        ("drawings_cash", "Drawings", "Cash"),
        ("loan_received", "Cash", "Loan Payable"),
        ("loan_repayment", "Loan Payable", "Cash"),
    ],
)
def test_template_accounts(template_id, debit, credit):
    template = get_template(template_id)

    assert template.debit_account == debit
    assert template.credit_account == credit
    assert template.accounts() == (debit, credit)


def test_unknown_template_raises():
    with pytest.raises(KeyError):
        get_template("does_not_exist")


def test_category_filter():
    sales = get_templates_by_category(TemplateCategory.SALES)

    assert sales
    assert all(
        template.category == TemplateCategory.SALES
        for template in sales
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Cash sale Rs. 10,000", Decimal("10000")),
        ("Purchase ₹5,500", Decimal("5500")),
        ("Rent paid 2500", Decimal("2500")),
        ("Salary paid $1000", Decimal("1000")),
        ("No amount here", None),
    ],
)
def test_extract_amount(text, expected):
    assert extract_amount(text) == expected


@pytest.mark.parametrize(
    "text,template_id",
    [
        ("Cash sale of goods for Rs 10000", "cash_sale"),
        ("Goods sold on credit for 25000", "credit_sale"),
        ("Purchased goods for cash 5000", "cash_purchase"),
        ("Purchased goods on credit 12000", "credit_purchase"),
        ("Rent paid 3000", "rent_paid"),
        ("Salary paid 15000", "salary_paid"),
        ("Electricity bill paid 2200", "electricity_paid"),
        ("Commission received 5000", "commission_received"),
        ("Capital introduced 50000", "capital_introduced"),
        ("Owner drawings 2000", "drawings_cash"),
        ("Loan received 100000", "loan_received"),
        ("Repaid loan 10000", "loan_repayment"),
        ("Cash deposited in bank 5000", "cash_deposited_bank"),
        ("Cash withdrawn from bank 3000", "cash_withdrawn_bank"),
        ("Bad debt written off 4000", "bad_debt"),
    ],
)
def test_match_template(text, template_id):
    result = match_template(text)

    assert result is not None
    assert result.template_id == template_id
    assert result.is_valid
    assert result.confidence > Decimal("0")
    assert result.matched_keywords


def test_unmatched_transaction_returns_none():
    assert match_template("Something completely unrelated") is None


def test_resolve_template():
    template = resolve_template("Cash sale for Rs 5000")

    assert template.template_id == "cash_sale"
    assert template.debit_account == "Cash"
    assert template.credit_account == "Sales"


def test_resolve_unknown_template_raises():
    with pytest.raises(LookupError):
        resolve_template("Something completely unrelated")


def test_template_amount_validation():
    template = get_template("cash_sale")

    assert template.validate_amount(Decimal("100"))
    assert not template.validate_amount(Decimal("0"))
    assert not template.validate_amount(Decimal("-10"))


def test_template_flags():
    cash_sale = get_template("cash_sale")
    credit_sale = get_template("credit_sale")

    assert cash_sale.supports_cash
    assert not cash_sale.supports_credit

    assert not credit_sale.supports_cash
    assert credit_sale.supports_credit
