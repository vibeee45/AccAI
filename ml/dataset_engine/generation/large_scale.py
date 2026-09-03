from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from .generator import generate_transactions


def _record_to_dict(record: Any) -> dict:
    if is_dataclass(record):
        return asdict(record)

    if isinstance(record, dict):
        return dict(record)

    return {
        key: value
        for key, value in vars(record).items()
    }


def generate_in_chunks(
    rows: int,
    chunk_size: int = 100_000,
    seed: int = 42,
) -> Iterator[tuple]:
    """
    Generate transactions lazily in chunks.

    Only one chunk is kept in memory at a time.
    """

    if rows < 0:
        raise ValueError("rows must be >= 0")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    generated = 0
    chunk_index = 0

    while generated < rows:
        current_size = min(
            chunk_size,
            rows - generated,
        )

        chunk_seed = seed + chunk_index

        chunk = generate_transactions(
            rows=current_size,
            seed=chunk_seed,
        )

        yield tuple(chunk)

        generated += current_size
        chunk_index += 1


def write_csv(
    records: Iterator[tuple],
    path: str | Path,
) -> int:
    """
    Write generated records to CSV incrementally.
    """

    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_written = 0
    writer = None

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        for chunk in records:
            for record in chunk:
                row = _record_to_dict(record)

                if writer is None:
                    fieldnames = list(row.keys())
                    writer = csv.DictWriter(
                        file,
                        fieldnames=fieldnames,
                    )
                    writer.writeheader()

                writer.writerow(row)
                rows_written += 1

    return rows_written


def write_jsonl(
    records: Iterator[tuple],
    path: str | Path,
) -> int:
    """
    Write generated records to JSON Lines incrementally.
    """

    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_written = 0

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for chunk in records:
            for record in chunk:
                row = _record_to_dict(record)

                file.write(
                    json.dumps(
                        row,
                        default=str,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                rows_written += 1

    return rows_written


def generate_to_csv(
    rows: int,
    path: str | Path,
    chunk_size: int = 100_000,
    seed: int = 42,
) -> int:
    return write_csv(
        generate_in_chunks(
            rows=rows,
            chunk_size=chunk_size,
            seed=seed,
        ),
        path,
    )


def generate_to_jsonl(
    rows: int,
    path: str | Path,
    chunk_size: int = 100_000,
    seed: int = 42,
) -> int:
    return write_jsonl(
        generate_in_chunks(
            rows=rows,
            chunk_size=chunk_size,
            seed=seed,
        ),
        path,
    )
