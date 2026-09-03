from __future__ import annotations

from collections import Counter
from typing import Any


def get_field(record: Any, field: str):
    if isinstance(record, dict):
        return record.get(field)

    return getattr(record, field, None)


def class_distribution(
    records: list[Any] | tuple[Any, ...],
    field: str = "template_id",
) -> dict[str, int]:
    values = []

    for record in records:
        value = get_field(record, field)

        if value is not None:
            values.append(str(value))

    return dict(Counter(values))


def distribution_difference(
    expected: dict[str, int],
    actual: dict[str, int],
) -> dict[str, int]:
    keys = set(expected) | set(actual)

    return {
        key: actual.get(key, 0) - expected.get(key, 0)
        for key in sorted(keys)
    }
