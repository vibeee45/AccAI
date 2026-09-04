import pytest

from ml.transaction_understanding.debit_credit import (
    DebitCredit,
    DebitCreditConfig,
    DebitCreditPredictor,
    DebitCreditService,
    get_direction,
    get_reason,
    has_rule,
)


def create_predictor():
    return DebitCreditPredictor(
        DebitCreditConfig(
            confidence_threshold=0.80,
            rule_confidence=0.98,
            fallback_confidence=0.50,
        )
    )


def test_config_defaults():
    config = DebitCreditConfig()

    assert config.confidence_threshold == 0.80
    assert config.rule_confidence == 0.98


def test_config_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        DebitCreditConfig(
            confidence_threshold=1.5
        )


def test_config_rejects_invalid_rule_confidence():
    with pytest.raises(ValueError):
        DebitCreditConfig(
            rule_confidence=-0.1
        )


def test_cash_is_debit():
    assert get_direction("cash") == (
        DebitCredit.DEBIT
    )


def test_bank_is_debit():
    assert get_direction("bank") == (
        DebitCredit.DEBIT
    )


def test_receivables_are_debit():
    assert get_direction(
        "accounts_receivable"
    ) == DebitCredit.DEBIT


def test_inventory_is_debit():
    assert get_direction("inventory") == (
        DebitCredit.DEBIT
    )


def test_furniture_is_debit():
    assert get_direction("furniture") == (
        DebitCredit.DEBIT
    )


def test_machinery_is_debit():
    assert get_direction("machinery") == (
        DebitCredit.DEBIT
    )


def test_office_equipment_is_debit():
    assert get_direction(
        "office_equipment"
    ) == DebitCredit.DEBIT


def test_computer_equipment_is_debit():
    assert get_direction(
        "computer_equipment"
    ) == DebitCredit.DEBIT


def test_payables_are_credit():
    assert get_direction(
        "accounts_payable"
    ) == DebitCredit.CREDIT


def test_loan_is_credit():
    assert get_direction("loan") == (
        DebitCredit.CREDIT
    )


def test_capital_is_credit():
    assert get_direction("capital") == (
        DebitCredit.CREDIT
    )


def test_sales_are_credit():
    assert get_direction("sales") == (
        DebitCredit.CREDIT
    )


def test_commission_income_is_credit():
    assert get_direction(
        "commission_income"
    ) == DebitCredit.CREDIT


def test_interest_income_is_credit():
    assert get_direction(
        "interest_income"
    ) == DebitCredit.CREDIT


def test_purchases_are_debit():
    assert get_direction("purchases") == (
        DebitCredit.DEBIT
    )


def test_rent_is_debit():
    assert get_direction(
        "rent_expense"
    ) == DebitCredit.DEBIT


def test_salary_is_debit():
    assert get_direction(
        "salary_expense"
    ) == DebitCredit.DEBIT


def test_utilities_are_debit():
    assert get_direction(
        "utilities_expense"
    ) == DebitCredit.DEBIT


def test_tax_is_debit():
    assert get_direction(
        "tax_expense"
    ) == DebitCredit.DEBIT


def test_insurance_is_debit():
    assert get_direction(
        "insurance_expense"
    ) == DebitCredit.DEBIT


def test_known_account_has_rule():
    assert has_rule("rent_expense") is True


def test_unknown_account_has_no_rule():
    assert has_rule(
        "unknown_account"
    ) is False


def test_reason_exists_for_known_account():
    reason = get_reason(
        "rent_expense"
    )

    assert reason
    assert "expense" in reason.lower()


def test_unknown_account_reason():
    reason = get_reason(
        "unknown_account"
    )

    assert "No explicit accounting rule" in reason


def test_predict_rent_as_debit():
    predictor = create_predictor()

    result = predictor.predict(
        "rent_expense",
        "Rent Expense",
    )

    assert result.direction == (
        DebitCredit.DEBIT
    )

    assert result.confidence == 0.98
    assert result.requires_review is False


def test_predict_sales_as_credit():
    predictor = create_predictor()

    result = predictor.predict(
        "sales",
        "Sales",
    )

    assert result.direction == (
        DebitCredit.CREDIT
    )

    assert result.confidence == 0.98


def test_predict_bank_as_debit():
    predictor = create_predictor()

    result = predictor.predict(
        "bank",
        "Bank",
    )

    assert result.direction == (
        DebitCredit.DEBIT
    )


def test_predict_capital_as_credit():
    predictor = create_predictor()

    result = predictor.predict(
        "capital",
        "Capital",
    )

    assert result.direction == (
        DebitCredit.CREDIT
    )


def test_predict_unknown_account_requires_review():
    predictor = create_predictor()

    result = predictor.predict(
        "unknown_account",
        "Unknown Account",
    )

    assert result.direction == (
        DebitCredit.DEBIT
    )

    assert result.confidence == 0.50
    assert result.requires_review is True


def test_unknown_account_reason_requires_review():
    predictor = create_predictor()

    result = predictor.predict(
        "unknown_account",
        "Unknown Account",
    )

    assert "human review" in (
        result.reason.lower()
    )


def test_prediction_contains_account_information():
    predictor = create_predictor()

    result = predictor.predict(
        "rent_expense",
        "Rent Expense",
    )

    assert result.account_id == "rent_expense"
    assert result.account_name == "Rent Expense"


def test_prediction_confidence_range():
    predictor = create_predictor()

    result = predictor.predict(
        "rent_expense",
        "Rent Expense",
    )

    assert 0 <= result.confidence <= 1


def test_predict_pair():
    predictor = create_predictor()

    result = predictor.predict_pair(
        debit_account_id="rent_expense",
        debit_account_name="Rent Expense",
        credit_account_id="bank",
        credit_account_name="Bank",
    )

    assert result.debit_account_id == (
        "rent_expense"
    )

    assert result.credit_account_id == (
        "bank"
    )

    assert result.confidence == 0.98
    assert result.requires_review is False


def test_predict_pair_rejects_credit_account_as_debit():
    predictor = create_predictor()

    with pytest.raises(ValueError):
        predictor.predict_pair(
            debit_account_id="sales",
            debit_account_name="Sales",
            credit_account_id="bank",
            credit_account_name="Bank",
        )


def test_predict_pair_rejects_debit_account_as_credit():
    predictor = create_predictor()

    with pytest.raises(ValueError):
        predictor.predict_pair(
            debit_account_id="rent_expense",
            debit_account_name="Rent Expense",
            credit_account_id="cash",
            credit_account_name="Cash",
        )


def test_predict_pair_rejects_same_account():
    predictor = create_predictor()

    with pytest.raises(ValueError):
        predictor.predict_pair(
            debit_account_id="bank",
            debit_account_name="Bank",
            credit_account_id="bank",
            credit_account_name="Bank",
        )


def test_predict_many():
    predictor = create_predictor()

    results = predictor.predict_many(
        [
            ("rent_expense", "Rent Expense"),
            ("sales", "Sales"),
            ("bank", "Bank"),
        ]
    )

    assert len(results) == 3

    assert results[0].direction == (
        DebitCredit.DEBIT
    )

    assert results[1].direction == (
        DebitCredit.CREDIT
    )

    assert results[2].direction == (
        DebitCredit.DEBIT
    )


def test_predict_many_rejects_empty():
    predictor = create_predictor()

    with pytest.raises(ValueError):
        predictor.predict_many([])


def test_predict_rejects_empty_account_id():
    predictor = create_predictor()

    with pytest.raises(ValueError):
        predictor.predict(
            "",
            "Rent Expense",
        )


def test_predict_rejects_empty_account_name():
    predictor = create_predictor()

    with pytest.raises(ValueError):
        predictor.predict(
            "rent_expense",
            "",
        )


def test_predict_rejects_non_string_account_id():
    predictor = create_predictor()

    with pytest.raises(TypeError):
        predictor.predict(
            None,
            "Rent Expense",
        )


def test_predict_rejects_non_string_account_name():
    predictor = create_predictor()

    with pytest.raises(TypeError):
        predictor.predict(
            "rent_expense",
            None,
        )


def test_service_is_ready():
    service = DebitCreditService()

    assert service.ready is True


def test_service_predict():
    service = DebitCreditService()

    result = service.predict(
        "rent_expense",
        "Rent Expense",
    )

    assert result.direction == (
        DebitCredit.DEBIT
    )


def test_service_predict_pair():
    service = DebitCreditService()

    result = service.predict_pair(
        debit_account_id="rent_expense",
        debit_account_name="Rent Expense",
        credit_account_id="bank",
        credit_account_name="Bank",
    )

    assert result.debit_account_id == (
        "rent_expense"
    )

    assert result.credit_account_id == (
        "bank"
    )


def test_service_predict_many():
    service = DebitCreditService()

    results = service.predict_many(
        [
            ("cash", "Cash"),
            ("sales", "Sales"),
        ]
    )

    assert len(results) == 2


def test_prediction_reason_is_present():
    predictor = create_predictor()

    result = predictor.predict(
        "sales",
        "Sales",
    )

    assert result.reason
