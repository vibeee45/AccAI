from datetime import date
from decimal import Decimal

import pytest

from ml.dataset_engine.generation import (
    GenerationConfig,
    TransactionGenerator,
    generate_transactions,
)


def test_default_generation_count():
    transactions = generate_transactions(rows=10)

    assert len(transactions) == 10


def test_zero_rows():
    transactions = generate_transactions(rows=0)

    assert transactions == []


def test_generated_transaction_fields():
    transaction = generate_transactions(rows=1)[0]

    assert transaction.transaction_id
    assert transaction.date
    assert transaction.transaction
    assert transaction.amount > Decimal("0")
    assert transaction.template_id
    assert transaction.debit_account
    assert transaction.credit_account
    assert transaction.category


def test_amount_is_within_configured_range():
    transactions = generate_transactions(
        rows=100,
        min_amount=Decimal("500"),
        max_amount=Decimal("5000"),
    )

    for transaction in transactions:
        assert Decimal("500") <= transaction.amount <= Decimal("5000")


def test_dates_are_within_configured_range():
    transactions = generate_transactions(
        rows=100,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )

    for transaction in transactions:
        assert date(2026, 3, 1) <= transaction.date <= date(2026, 3, 31)


def test_same_seed_produces_same_dataset():
    first = generate_transactions(rows=100, seed=123)
    second = generate_transactions(rows=100, seed=123)

    assert first == second


def test_different_seed_produces_different_dataset():
    first = generate_transactions(rows=100, seed=123)
    second = generate_transactions(rows=100, seed=456)

    assert first != second


def test_transaction_ids_are_unique():
    transactions = generate_transactions(rows=1000)

    ids = [transaction.transaction_id for transaction in transactions]

    assert len(ids) == len(set(ids))


def test_transaction_ids_contain_seed():
    transactions = generate_transactions(rows=2, seed=123)

    assert transactions[0].transaction_id.startswith("GEN-00000123-")


def test_every_generated_transaction_is_valid():
    transactions = generate_transactions(rows=500)

    for transaction in transactions:
        transaction.validate()


def test_generated_accounts_match_template():
    from ml.dataset_engine.templates import get_template

    transactions = generate_transactions(rows=500)

    for transaction in transactions:
        template = get_template(transaction.template_id)

        assert transaction.debit_account == template.debit_account
        assert transaction.credit_account == template.credit_account
        assert transaction.category == template.category.value


def test_config_validation_negative_rows():
    config = GenerationConfig(rows=-1)

    with pytest.raises(ValueError):
        config.validate()


def test_config_validation_invalid_dates():
    config = GenerationConfig(
        start_date=date(2026, 12, 31),
        end_date=date(2026, 1, 1),
    )

    with pytest.raises(ValueError):
        config.validate()


def test_config_validation_invalid_amount():
    config = GenerationConfig(
        min_amount=Decimal("0"),
    )

    with pytest.raises(ValueError):
        config.validate()


def test_config_validation_reversed_amount_range():
    config = GenerationConfig(
        min_amount=Decimal("5000"),
        max_amount=Decimal("1000"),
    )

    with pytest.raises(ValueError):
        config.validate()


def test_single_day_generation():
    transactions = generate_transactions(
        rows=50,
        start_date=date(2026, 5, 15),
        end_date=date(2026, 5, 15),
    )

    assert all(
        transaction.date == date(2026, 5, 15)
        for transaction in transactions
    )


def test_decimal_amounts_have_max_two_decimal_places():
    transactions = generate_transactions(rows=100)

    for transaction in transactions:
        assert transaction.amount.as_tuple().exponent >= -2


def test_generator_object_reproducibility():
    config = GenerationConfig(rows=50, seed=999)

    first = TransactionGenerator(config).generate()
    second = TransactionGenerator(config).generate()

    assert first == second


def test_generator_respects_row_count():
    for count in [1, 5, 25, 100]:
        transactions = TransactionGenerator(
            GenerationConfig(rows=count)
        ).generate()

        assert len(transactions) == count


def test_generated_text_contains_amount():
    transactions = generate_transactions(rows=100)

    for transaction in transactions:
        assert str(transaction.amount) in transaction.transaction
