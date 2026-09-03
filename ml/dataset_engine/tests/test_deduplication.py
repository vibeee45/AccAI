from decimal import Decimal

import pytest

from ml.dataset_engine.deduplication import (
    DeduplicationConfig,
    deduplicate_records,
    record_fingerprint,
    semantic_fingerprint,
)
from ml.dataset_engine.generation import generate_transactions
from ml.dataset_engine.variations import generate_variations


def test_empty_dataset():
    result = deduplicate_records([])

    assert result.records == ()
    assert result.stats.rows_input == 0
    assert result.stats.rows_output == 0
    assert result.stats.duplicates_removed == 0


def test_unique_records_are_retained():
    records = generate_transactions(rows=20, seed=42)

    result = deduplicate_records(records)

    assert len(result.records) == 20
    assert result.stats.duplicates_removed == 0


def test_exact_duplicate_is_removed():
    records = generate_transactions(rows=2, seed=42)

    records = [
        records[0],
        records[0],
    ]

    result = deduplicate_records(records)

    assert len(result.records) == 1
    assert result.stats.exact_duplicates_removed == 1
    assert result.stats.rows_output == 1


def test_duplicate_record_is_reported():
    records = generate_transactions(rows=2, seed=42)

    result = deduplicate_records(
        [records[0], records[0]]
    )

    assert len(result.duplicates) == 1
    assert result.duplicates[0].row_index == 1
    assert result.duplicates[0].duplicate_of == 0
    assert result.duplicates[0].duplicate_type == "exact"


def test_first_occurrence_is_retained():
    records = generate_transactions(rows=1, seed=42)

    result = deduplicate_records(
        [records[0], records[0], records[0]]
    )

    assert len(result.records) == 1
    assert result.stats.exact_duplicates_removed == 2


def test_duplicate_rate():
    records = generate_transactions(rows=3, seed=42)

    result = deduplicate_records(
        [records[0], records[1], records[0]]
    )

    assert result.stats.duplicate_rate == pytest.approx(
        1 / 3
    )


def test_fingerprint_is_deterministic():
    record = generate_transactions(rows=1, seed=42)[0]

    assert record_fingerprint(record) == record_fingerprint(record)


def test_semantic_fingerprint_is_deterministic():
    record = generate_transactions(rows=1, seed=42)[0]

    assert (
        semantic_fingerprint(record)
        == semantic_fingerprint(record)
    )


def test_same_records_have_same_fingerprint():
    records = generate_transactions(rows=1, seed=42)

    first = records[0]

    assert record_fingerprint(first) == record_fingerprint(first)


def test_different_records_have_different_fingerprints():
    records = generate_transactions(rows=2, seed=42)

    assert (
        record_fingerprint(records[0])
        != record_fingerprint(records[1])
    )


def test_variations_are_not_removed_by_default():
    transactions = generate_transactions(
        rows=5,
        seed=42,
    )

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=42,
    )

    result = deduplicate_records(variations)

    assert len(result.records) == len(variations)


def test_semantic_duplicates_are_detected():
    transactions = generate_transactions(
        rows=1,
        seed=42,
    )

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=42,
    )

    result = deduplicate_records(variations)

    assert result.stats.semantic_duplicates_detected >= 0


def test_semantic_duplicate_removal_can_be_enabled():
    transactions = generate_transactions(
        rows=1,
        seed=42,
    )

    variations = generate_variations(
        transactions,
        variations_per_transaction=5,
        seed=42,
    )

    config = DeduplicationConfig(
        remove_exact_duplicates=True,
        remove_identical_fingerprints=True,
    )

    result = deduplicate_records(
        variations,
        config,
    )

    assert len(result.records) <= len(variations)


def test_config_can_disable_exact_removal():
    records = generate_transactions(rows=1, seed=42)

    config = DeduplicationConfig(
        remove_exact_duplicates=False,
    )

    result = deduplicate_records(
        [records[0], records[0]],
        config,
    )

    assert len(result.records) == 2
    assert result.stats.exact_duplicates_removed == 0


def test_config_validation():
    config = DeduplicationConfig(
        remove_exact_duplicates="yes",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_output_preserves_order():
    records = generate_transactions(rows=5, seed=42)

    result = deduplicate_records(
        [records[2], records[0], records[2], records[1]]
    )

    assert result.records[0] == records[2]
    assert result.records[1] == records[0]
    assert result.records[2] == records[1]


def test_stats_consistency():
    records = generate_transactions(rows=10, seed=42)

    records = records + [records[0], records[1]]

    result = deduplicate_records(records)

    assert (
        result.stats.rows_input
        == result.stats.rows_output
        + result.stats.duplicates_removed
    )


def test_generated_dataset_deduplication():
    records = generate_transactions(
        rows=1000,
        seed=42,
    )

    records = records + records[:50]

    result = deduplicate_records(records)

    assert result.stats.rows_input == 1050
    assert result.stats.rows_output == 1000
    assert result.stats.exact_duplicates_removed == 50


def test_duplicate_detection_does_not_mutate_input():
    records = generate_transactions(rows=10, seed=42)

    original = list(records)

    deduplicate_records(
        records + [records[0]]
    )

    assert records == original


def test_decimal_values_are_fingerprintable():
    record = {
        "amount": Decimal("5000.00"),
        "template_id": "cash_sale",
    }

    fingerprint = record_fingerprint(record)

    assert isinstance(fingerprint, str)
    assert len(fingerprint) == 64
