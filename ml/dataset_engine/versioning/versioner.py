from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .schemas import (
    DatasetVersion,
    DatasetVersionConfig,
)


def _normalize_record(record: Any) -> str:
    if hasattr(record, "__dataclass_fields__"):
        data = {
            field: getattr(record, field)
            for field in record.__dataclass_fields__
        }
    elif isinstance(record, dict):
        data = dict(record)
    else:
        data = {
            key: value
            for key, value in vars(record).items()
        }

    return json.dumps(
        data,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )


def calculate_dataset_checksum(
    records: list[Any] | tuple[Any, ...],
) -> str:
    hasher = hashlib.sha256()

    for record in records:
        normalized = _normalize_record(record)
        hasher.update(normalized.encode("utf-8"))
        hasher.update(b"\n")

    return hasher.hexdigest()


def create_dataset_version(
    config: DatasetVersionConfig,
    train: list[Any] | tuple[Any, ...],
    validation: list[Any] | tuple[Any, ...],
    test: list[Any] | tuple[Any, ...],
) -> DatasetVersion:
    config.validate()

    train = tuple(train)
    validation = tuple(validation)
    test = tuple(test)

    total_rows = (
        len(train)
        + len(validation)
        + len(test)
    )

    all_records = train + validation + test

    checksum = calculate_dataset_checksum(
        all_records
    )

    return DatasetVersion(
        dataset_name=config.dataset_name,
        version=config.version,
        seed=config.seed,
        source=config.source,
        description=config.description,
        created_at=datetime.now(timezone.utc),
        total_rows=total_rows,
        train_rows=len(train),
        validation_rows=len(validation),
        test_rows=len(test),
        checksum=checksum,
    )
