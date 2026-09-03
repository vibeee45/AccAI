from decimal import Decimal
from uuid import uuid4

import pytest

from app.accounting.normalization import (
    NormalizationError,
    normalize_amount,
    normalize_transaction,
)
from app.accounting.validators import (
    AccountingValidationError,
    validate_balanced_entry,
)
from app.accounting.journal import generate_journal


def test_normalize_integer_amount():
    assert normalize_amount(50000) == Decimal("50000.00")


def test_normalize_comma_amount():
    assert normalize_amount("50,000") == Decimal("50000.00")


def test_normalize_rupee_amount():
    assert normalize_amount("₹50,000") == Decimal("50000.00")


def test_normalize_k_amount():
    assert normalize_amount("50K") == Decimal("50000.00")


def test_normalize_lakh_amount():
    assert normalize_amount("1.5L") == Decimal("150000.00")


def test_negative_amount_rejected():
    with pytest.raises(NormalizationError):
        normalize_amount("-5000")


def test_invalid_amount_rejected():
    with pytest.raises(NormalizationError):
        normalize_amount("abc")


def test_normalize_transaction():
    transaction = normalize_transaction(
        transaction_id=uuid4(),
        transaction_date="03-09-2026",
        description="  Purchased   goods for cash  ",
        amount="₹50,000",
        transaction_type="purchase",
        debit_account="Purchases",
        credit_account="Cash",
    )

    assert transaction.amount == Decimal("50000.00")
    assert transaction.description == "Purchased goods for cash"
    assert transaction.transaction_type == "PURCHASE"
    assert transaction.debit_account == "Purchases"
    assert transaction.credit_account == "Cash"


def test_balanced_entry():
    validate_balanced_entry(
        [
            (Decimal("50000.00"), Decimal("0.00")),
            (Decimal("0.00"), Decimal("50000.00")),
        ]
    )


def test_unbalanced_entry_rejected():
    with pytest.raises(AccountingValidationError):
        validate_balanced_entry(
            [
                (Decimal("50000.00"), Decimal("0.00")),
                (Decimal("0.00"), Decimal("40000.00")),
            ]
        )


def test_both_debit_and_credit_rejected():
    with pytest.raises(AccountingValidationError):
        validate_balanced_entry(
            [
                (Decimal("50000.00"), Decimal("10000.00")),
                (Decimal("0.00"), Decimal("40000.00")),
            ]
        )


def test_journal_generation():
    transaction = normalize_transaction(
        transaction_id=uuid4(),
        transaction_date="2026-09-03",
        description="Purchased goods for cash",
        amount="50000",
        transaction_type="PURCHASE",
        debit_account="Purchases",
        credit_account="Cash",
    )

    journal = generate_journal(transaction)

    assert len(journal.lines) == 2
    assert journal.total_debit == Decimal("50000.00")
    assert journal.total_credit == Decimal("50000.00")
    assert journal.is_balanced is True

    assert journal.lines[0].account == "Purchases"
    assert journal.lines[0].debit == Decimal("50000.00")

    assert journal.lines[1].account == "Cash"
    assert journal.lines[1].credit == Decimal("50000.00")


def test_same_debit_credit_account_rejected():
    transaction = normalize_transaction(
        transaction_id=uuid4(),
        transaction_date="2026-09-03",
        description="Invalid transaction",
        amount=50000,
        debit_account="Cash",
        credit_account="Cash",
    )

    with pytest.raises(AccountingValidationError):
        generate_journal(transaction)


def test_zero_amount_rejected_by_journal():
    transaction = normalize_transaction(
        transaction_id=uuid4(),
        transaction_date="2026-09-03",
        description="Zero transaction",
        amount=0,
        debit_account="Purchases",
        credit_account="Cash",
    )

    with pytest.raises(AccountingValidationError):
        generate_journal(transaction)