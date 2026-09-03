import pytest

from ml.dataset_engine.generation import generate_transactions
from ml.dataset_engine.splitting import (
    SplitConfig,
    class_distribution,
    split_dataset,
)


def test_empty_dataset():
    result = split_dataset([])

    assert result.train == ()
    assert result.validation == ()
    assert result.test == ()
    assert result.statistics.total_rows == 0


def test_default_split():
    records = generate_transactions(
        rows=1000,
        seed=42,
    )

    result = split_dataset(records)

    assert result.statistics.total_rows == 1000
    assert len(result.train) + len(result.validation) + len(result.test) == 1000


def test_approximately_80_10_10_split():
    records = generate_transactions(
        rows=1000,
        seed=42,
    )

    result = split_dataset(records)

    assert len(result.train) == 800
    assert len(result.validation) == 100
    assert len(result.test) == 100


def test_custom_ratios():
    records = generate_transactions(
        rows=1000,
        seed=42,
    )

    config = SplitConfig(
        train_ratio=0.70,
        validation_ratio=0.15,
        test_ratio=0.15,
    )

    result = split_dataset(records, config)

    assert len(result.train) == 700
    assert len(result.validation) == 150
    assert len(result.test) == 150


def test_ratios_must_sum_to_one():
    config = SplitConfig(
        train_ratio=0.70,
        validation_ratio=0.20,
        test_ratio=0.20,
    )

    with pytest.raises(ValueError):
        config.validate()


def test_ratios_must_be_positive():
    config = SplitConfig(
        train_ratio=0.0,
        validation_ratio=0.5,
        test_ratio=0.5,
    )

    with pytest.raises(ValueError):
        config.validate()


def test_split_is_reproducible():
    records = generate_transactions(
        rows=500,
        seed=42,
    )

    config = SplitConfig(seed=123)

    first = split_dataset(records, config)
    second = split_dataset(records, config)

    assert first.train == second.train
    assert first.validation == second.validation
    assert first.test == second.test


def test_different_seed_changes_split():
    records = generate_transactions(
        rows=500,
        seed=42,
    )

    first = split_dataset(
        records,
        SplitConfig(seed=1),
    )

    second = split_dataset(
        records,
        SplitConfig(seed=2),
    )

    assert first.train != second.train


def test_all_records_are_preserved():
    records = generate_transactions(
        rows=500,
        seed=42,
    )

    result = split_dataset(records)

    combined = (
        list(result.train)
        + list(result.validation)
        + list(result.test)
    )

    assert len(combined) == len(records)
    assert set(combined) == set(records)


def test_splits_are_disjoint():
    records = generate_transactions(
        rows=500,
        seed=42,
    )

    result = split_dataset(records)

    train_ids = {record.transaction_id for record in result.train}
    validation_ids = {
        record.transaction_id for record in result.validation
    }
    test_ids = {
        record.transaction_id for record in result.test
    }

    assert train_ids.isdisjoint(validation_ids)
    assert train_ids.isdisjoint(test_ids)
    assert validation_ids.isdisjoint(test_ids)


def test_stratification_by_template():
    records = generate_transactions(
        rows=1000,
        seed=42,
    )

    result = split_dataset(records)

    full_distribution = class_distribution(records)
    train_distribution = class_distribution(result.train)
    validation_distribution = class_distribution(result.validation)
    test_distribution = class_distribution(result.test)

    assert set(train_distribution) == set(full_distribution)
    assert set(validation_distribution) == set(full_distribution)
    assert set(test_distribution) == set(full_distribution)


def test_class_distribution():
    records = generate_transactions(
        rows=100,
        seed=42,
    )

    distribution = class_distribution(records)

    assert sum(distribution.values()) == 100
    assert len(distribution) > 1


def test_can_disable_stratification():
    records = generate_transactions(
        rows=100,
        seed=42,
    )

    config = SplitConfig(
        stratify_by=None,
    )

    result = split_dataset(records, config)

    assert (
        len(result.train)
        + len(result.validation)
        + len(result.test)
        == 100
    )


def test_missing_stratification_field():
    records = [
        {"transaction": "Cash sale", "amount": 5000},
        {"transaction": "Rent paid", "amount": 2000},
    ]

    with pytest.raises(ValueError):
        split_dataset(records)


def test_dictionary_records_supported():
    records = [
        {
            "transaction_id": str(index),
            "template_id": "cash_sale",
        }
        for index in range(100)
    ]

    result = split_dataset(records)

    assert len(result.train) == 80
    assert len(result.validation) == 10
    assert len(result.test) == 10


def test_statistics_ratios():
    records = generate_transactions(
        rows=1000,
        seed=42,
    )

    result = split_dataset(records)

    assert result.statistics.train_ratio == pytest.approx(0.8)
    assert result.statistics.validation_ratio == pytest.approx(0.1)
    assert result.statistics.test_ratio == pytest.approx(0.1)


def test_seed_must_be_integer():
    config = SplitConfig(seed="42")

    with pytest.raises(ValueError):
        config.validate()


def test_statistics_match_actual_output():
    records = generate_transactions(
        rows=257,
        seed=42,
    )

    result = split_dataset(records)

    assert result.statistics.train_rows == len(result.train)
    assert result.statistics.validation_rows == len(result.validation)
    assert result.statistics.test_rows == len(result.test)


def test_small_dataset_does_not_crash():
    records = generate_transactions(
        rows=5,
        seed=42,
    )

    result = split_dataset(records)

    assert (
        len(result.train)
        + len(result.validation)
        + len(result.test)
        == 5
    )
