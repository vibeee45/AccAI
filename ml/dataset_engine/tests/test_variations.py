from decimal import Decimal

import pytest

from ml.dataset_engine.generation import generate_transactions
from ml.dataset_engine.variations import (
    VariationConfig,
    VariationGenerator,
    generate_variations,
    get_variation_phrases,
    normalize_for_comparison,
    normalize_variation,
)


def test_variation_catalog_is_not_empty():
    assert get_variation_phrases("cash_sale")


def test_unknown_template_has_no_variations():
    assert get_variation_phrases("unknown_template") == ()


def test_generate_variations_count():
    transactions = generate_transactions(rows=10, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=42,
    )

    assert len(variations) == 50


def test_variations_preserve_template():
    transactions = generate_transactions(rows=20, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    assert all(
        variation.template_id
        for variation in variations
    )


def test_variations_preserve_amount():
    transactions = generate_transactions(rows=10, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    amounts = {
        transaction.transaction_id: transaction.amount
        for transaction in transactions
    }

    for variation in variations:
        assert (
            variation.amount
            == amounts[variation.source_transaction_id]
        )


def test_variations_preserve_accounts():
    transactions = generate_transactions(rows=10, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    source = {
        transaction.transaction_id: transaction
        for transaction in transactions
    }

    for variation in variations:
        original = source[variation.source_transaction_id]

        assert variation.debit_account == original.debit_account
        assert variation.credit_account == original.credit_account
        assert variation.category == original.category


def test_variation_ids_are_unique():
    transactions = generate_transactions(rows=100, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    ids = [variation.variation_id for variation in variations]

    assert len(ids) == len(set(ids))


def test_same_seed_produces_same_variations():
    transactions = generate_transactions(rows=20, seed=42)

    first = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=100,
    )

    second = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=100,
    )

    assert first == second


def test_different_seed_changes_variations():
    transactions = generate_transactions(rows=20, seed=42)

    first = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=100,
    )

    second = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=200,
    )

    assert first != second


def test_variation_contains_amount_by_default():
    transactions = generate_transactions(rows=1, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=3,
    )

    for variation in variations:
        assert str(variation.amount) in variation.transaction


def test_amount_can_be_excluded():
    transactions = generate_transactions(rows=1, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=3,
        include_amount=False,
    )

    for variation in variations:
        assert str(variation.amount) not in variation.transaction


def test_variation_is_valid():
    transactions = generate_transactions(rows=20, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    for variation in variations:
        variation.validate()


def test_config_validation():
    config = VariationConfig(
        variations_per_transaction=0
    )

    with pytest.raises(ValueError):
        config.validate()


def test_generator_object():
    transactions = generate_transactions(rows=5)

    generator = VariationGenerator(
        VariationConfig(
            variations_per_transaction=3,
            seed=42,
        )
    )

    variations = generator.generate(transactions)

    assert len(variations) == 15


def test_each_source_has_requested_number():
    transactions = generate_transactions(rows=20, seed=42)

    variations = generate_variations(
        transactions,
        variations_per_transaction=4,
    )

    counts = {}

    for variation in variations:
        counts[variation.source_transaction_id] = (
            counts.get(variation.source_transaction_id, 0) + 1
        )

    assert all(count == 4 for count in counts.values())


def test_variations_are_non_empty():
    transactions = generate_transactions(rows=20)

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    assert all(
        variation.transaction.strip()
        for variation in variations
    )


def test_normalize_variation():
    assert (
        normalize_variation("  Purchased   Goods  ₹5,000  ")
        == "purchased goods ₹5,000"
    )


def test_normalize_for_comparison():
    result = normalize_for_comparison(
        "Purchased goods for Rs. 5,000"
    )

    assert result == "purchased goods for rs <amount>"


def test_decimal_amount_is_preserved():
    transactions = generate_transactions(
        rows=1,
        min_amount=Decimal("1234"),
        max_amount=Decimal("1234"),
    )

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
    )

    assert all(
        variation.amount == Decimal("1234")
        for variation in variations
    )


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
def test_all_templates_have_natural_language_variations(template_id):
    phrases = get_variation_phrases(template_id)

    assert len(phrases) >= 5
    assert all(phrase.strip() for phrase in phrases)
