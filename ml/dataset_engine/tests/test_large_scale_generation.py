import json

import pytest

from ml.dataset_engine.generation import (
    benchmark_generation,
    generate_in_chunks,
    generate_to_csv,
    generate_to_jsonl,
)


def test_chunk_generation():
    chunks = list(
        generate_in_chunks(
            rows=25,
            chunk_size=10,
            seed=42,
        )
    )

    assert [len(chunk) for chunk in chunks] == [
        10,
        10,
        5,
    ]


def test_chunk_generation_preserves_total():
    chunks = generate_in_chunks(
        rows=103,
        chunk_size=20,
        seed=42,
    )

    total = sum(
        len(chunk)
        for chunk in chunks
    )

    assert total == 103


def test_chunk_size_larger_than_dataset():
    chunks = list(
        generate_in_chunks(
            rows=10,
            chunk_size=100,
            seed=42,
        )
    )

    assert len(chunks) == 1
    assert len(chunks[0]) == 10


def test_zero_rows():
    chunks = list(
        generate_in_chunks(
            rows=0,
            chunk_size=10,
        )
    )

    assert chunks == []


def test_negative_rows_rejected():
    with pytest.raises(ValueError):
        list(
            generate_in_chunks(
                rows=-1,
                chunk_size=10,
            )
        )


def test_invalid_chunk_size_rejected():
    with pytest.raises(ValueError):
        list(
            generate_in_chunks(
                rows=10,
                chunk_size=0,
            )
        )


def test_generation_is_reproducible():
    first = list(
        generate_in_chunks(
            rows=100,
            chunk_size=25,
            seed=42,
        )
    )

    second = list(
        generate_in_chunks(
            rows=100,
            chunk_size=25,
            seed=42,
        )
    )

    assert first == second


def test_different_seed_changes_output():
    first = list(
        generate_in_chunks(
            rows=100,
            chunk_size=25,
            seed=42,
        )
    )

    second = list(
        generate_in_chunks(
            rows=100,
            chunk_size=25,
            seed=99,
        )
    )

    assert first != second


def test_csv_generation(tmp_path):
    path = tmp_path / "transactions.csv"

    count = generate_to_csv(
        rows=100,
        path=path,
        chunk_size=25,
        seed=42,
    )

    assert count == 100
    assert path.exists()

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 101


def test_jsonl_generation(tmp_path):
    path = tmp_path / "transactions.jsonl"

    count = generate_to_jsonl(
        rows=100,
        path=path,
        chunk_size=25,
        seed=42,
    )

    assert count == 100
    assert path.exists()

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 100

    first = json.loads(lines[0])

    assert "transaction_id" in first
    assert "transaction" in first
    assert "amount" in first


def test_csv_creates_parent_directory(tmp_path):
    path = (
        tmp_path
        / "nested"
        / "data"
        / "transactions.csv"
    )

    count = generate_to_csv(
        rows=10,
        path=path,
        chunk_size=5,
    )

    assert count == 10
    assert path.exists()


def test_jsonl_creates_parent_directory(tmp_path):
    path = (
        tmp_path
        / "nested"
        / "data"
        / "transactions.jsonl"
    )

    count = generate_to_jsonl(
        rows=10,
        path=path,
        chunk_size=5,
    )

    assert count == 10
    assert path.exists()


def test_benchmark():
    result = benchmark_generation(
        rows=1000,
        chunk_size=100,
        seed=42,
    )

    assert result.rows == 1000
    assert result.chunk_size == 100
    assert result.elapsed_seconds >= 0
    assert result.rows_per_second > 0
    assert result.rows_per_minute > 0


def test_benchmark_rejects_zero():
    with pytest.raises(ValueError):
        benchmark_generation(
            rows=0,
        )


def test_benchmark_rejects_negative():
    with pytest.raises(ValueError):
        benchmark_generation(
            rows=-100,
        )


def test_large_chunk_generation():
    chunks = list(
        generate_in_chunks(
            rows=10_000,
            chunk_size=1_000,
            seed=42,
        )
    )

    assert len(chunks) == 10
    assert sum(len(chunk) for chunk in chunks) == 10_000


def test_csv_row_count_for_large_generation(tmp_path):
    path = tmp_path / "large.csv"

    count = generate_to_csv(
        rows=1_000,
        path=path,
        chunk_size=100,
        seed=42,
    )

    assert count == 1_000


def test_jsonl_row_count_for_large_generation(tmp_path):
    path = tmp_path / "large.jsonl"

    count = generate_to_jsonl(
        rows=1_000,
        path=path,
        chunk_size=100,
        seed=42,
    )

    assert count == 1_000
