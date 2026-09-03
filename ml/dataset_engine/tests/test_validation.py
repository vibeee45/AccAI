from datetime import date
from decimal import Decimal

import pytest

from ml.dataset_engine.generation import generate_transactions
from ml.dataset_engine.validation import (
    ValidationErrorType,
    format_report,
    summarize_errors,
    validate_dataset,
    validate_record,
)


def test_valid_generated_transaction():
    transaction = generate_transactions(
        rows=1,
        seed=42,
    )[0]

    result = validate_record(transaction)

    assert result.valid
    assert result.issues == ()


def test_generated_dataset_is_valid():
    transactions = generate_transactions(
        rows=100,
        seed=42,
    )

    report = validate_dataset(transactions)

    assert report.valid
    assert report.stats.rows_input == 100
    assert report.stats.rows_valid == 100
    assert report.stats.rows_invalid == 0
    assert report.stats.issues_found == 0


def test_missing_required_field():
    record = {
        "transaction_id": "TX-001",
        "date": date(2026, 1, 1),
        "transaction": "Cash sale",
        "amount": Decimal("1000"),
        "template_id": "cash_sale",
        "debit_account": "Cash",
        "credit_account": "Sales",
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.MISSING_FIELD
        for issue in result.issues
    )


def test_empty_transaction():
    transaction = generate_transactions(rows=1)[0]

    record = {
        "transaction_id": transaction.transaction_id,
        "date": transaction.date,
        "transaction": "   ",
        "amount": transaction.amount,
        "template_id": transaction.template_id,
        "debit_account": transaction.debit_account,
        "credit_account": transaction.credit_account,
        "category": transaction.category,
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.EMPTY_TRANSACTION
        for issue in result.issues
    )


def test_invalid_date():
    record = {
        "transaction_id": "TX-001",
        "date": "2026-01-01",
        "transaction": "Cash sale",
        "amount": Decimal("1000"),
        "template_id": "cash_sale",
        "debit_account": "Cash",
        "credit_account": "Sales",
        "category": "sales",
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.INVALID_DATE
        for issue in result.issues
    )


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-100"),
        "invalid",
        None,
    ],
)
def test_invalid_amount(amount):
    record = {
        "transaction_id": "TX-001",
        "date": date(2026, 1, 1),
        "transaction": "Cash sale",
        "amount": amount,
        "template_id": "cash_sale",
        "debit_account": "Cash",
        "credit_account": "Sales",
        "category": "sales",
    }

    result = validate_record(record)

    assert not result.valid


def test_unknown_template():
    record = {
        "transaction_id": "TX-001",
        "date": date(2026, 1, 1),
        "transaction": "Unknown transaction",
        "amount": Decimal("1000"),
        "template_id": "unknown",
        "debit_account": "Cash",
        "credit_account": "Sales",
        "category": "sales",
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.INVALID_TEMPLATE
        for issue in result.issues
    )


def test_template_debit_mismatch():
    record = {
        "transaction_id": "TX-001",
        "date": date(2026, 1, 1),
        "transaction": "Cash sale",
        "amount": Decimal("1000"),
        "template_id": "cash_sale",
        "debit_account": "Bank",
        "credit_account": "Sales",
        "category": "sales",
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.TEMPLATE_MISMATCH
        for issue in result.issues
    )


def test_template_credit_mismatch():
    record = {
        "transaction_id": "TX-001",
        "date": date(2026, 1, 1),
        "transaction": "Cash sale",
        "amount": Decimal("1000"),
        "template_id": "cash_sale",
        "debit_account": "Cash",
        "credit_account": "Purchases",
        "category": "sales",
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.TEMPLATE_MISMATCH
        for issue in result.issues
    )


def test_same_debit_and_credit():
    record = {
        "transaction_id": "TX-001",
        "date": date(2026, 1, 1),
        "transaction": "Something",
        "amount": Decimal("1000"),
        "template_id": "cash_sale",
        "debit_account": "Cash",
        "credit_account": "Cash",
        "category": "sales",
    }

    result = validate_record(record)

    assert not result.valid
    assert any(
        issue.error_type == ValidationErrorType.SAME_DEBIT_CREDIT
        for issue in result.issues
    )


def test_duplicate_transaction_ids():
    transactions = generate_transactions(
        rows=2,
        seed=42,
    )

    duplicate = transactions[1]

    records = [
        transactions[0],
        duplicate.__class__(
            transaction_id=transactions[0].transaction_id,
            date=duplicate.date,
            transaction=duplicate.transaction,
            amount=duplicate.amount,
            template_id=duplicate.template_id,
            debit_account=duplicate.debit_account,
            credit_account=duplicate.credit_account,
            category=duplicate.category,
        ),
    ]

    report = validate_dataset(records)

    assert not report.valid
    assert report.stats.rows_invalid == 1
    assert any(
        issue.error_type == ValidationErrorType.DUPLICATE_ID
        for issue in report.results[1].issues
    )


def test_validation_statistics():
    transactions = generate_transactions(
        rows=10,
        seed=42,
    )

    report = validate_dataset(transactions)

    assert report.stats.rows_input == 10
    assert report.stats.rows_valid == 10
    assert report.stats.rows_invalid == 0
    assert report.stats.issues_found == 0
    assert report.stats.validation_rate == 1.0


def test_empty_dataset():
    report = validate_dataset([])

    assert report.valid
    assert report.stats.rows_input == 0
    assert report.stats.rows_valid == 0
    assert report.stats.rows_invalid == 0
    assert report.stats.issues_found == 0
    assert report.stats.validation_rate == 0.0


def test_invalid_rows_property():
    transactions = generate_transactions(
        rows=2,
        seed=42,
    )

    records = list(transactions)

    records[1] = records[1].__class__(
        transaction_id=records[1].transaction_id,
        date=records[1].date,
        transaction="",
        amount=records[1].amount,
        template_id=records[1].template_id,
        debit_account=records[1].debit_account,
        credit_account=records[1].credit_account,
        category=records[1].category,
    )

    report = validate_dataset(records)

    assert len(report.invalid_rows) == 1
    assert report.invalid_rows[0].row_index == 1


def test_error_summary():
    transactions = generate_transactions(
        rows=2,
        seed=42,
    )

    records = list(transactions)

    records[0] = records[0].__class__(
        transaction_id=records[0].transaction_id,
        date=records[0].date,
        transaction="",
        amount=Decimal("-10"),
        template_id=records[0].template_id,
        debit_account=records[0].debit_account,
        credit_account=records[0].credit_account,
        category=records[0].category,
    )

    report = validate_dataset(records)

    errors = summarize_errors(report)

    assert errors["empty_transaction"] == 1
    assert errors["invalid_amount"] == 1


def test_formatted_report():
    transactions = generate_transactions(
        rows=5,
        seed=42,
    )

    report = validate_dataset(transactions)
    text = format_report(report)

    assert "ACCAI Dataset Validation Report" in text
    assert "Rows input:   5" in text
    assert "Rows valid:   5" in text
    assert "Rows invalid: 0" in text


def test_validation_result_is_row_specific():
    transaction = generate_transactions(
        rows=1,
        seed=42,
    )[0]

    result = validate_record(transaction, row_index=17)

    assert result.row_index == 17


def test_validation_handles_dataclass_records():
    transaction = generate_transactions(
        rows=1,
        seed=42,
    )[0]

    result = validate_record(transaction)

    result.validate()

    assert result.valid
