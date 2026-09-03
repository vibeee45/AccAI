from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from .schemas import DatasetSplit, SplitConfig, SplitStatistics
from .statistics import get_field


def _allocate_counts(
    total: int,
    ratios: tuple[float, float, float],
) -> tuple[int, int, int]:
    """
    Allocate an exact number of rows to train/validation/test.

    Uses the largest-remainder method so that:
        train + validation + test == total
    exactly.
    """

    raw = [
        total * ratio
        for ratio in ratios
    ]

    counts = [
        int(value)
        for value in raw
    ]

    remaining = total - sum(counts)

    remainders = sorted(
        range(3),
        key=lambda index: raw[index] - counts[index],
        reverse=True,
    )

    for index in remainders[:remaining]:
        counts[index] += 1

    return tuple(counts)


def _split_group(
    records: list[Any],
    config: SplitConfig,
    rng: random.Random,
) -> tuple[list[Any], list[Any], list[Any]]:
    shuffled = list(records)
    rng.shuffle(shuffled)

    train_count, validation_count, test_count = _allocate_counts(
        len(shuffled),
        (
            config.train_ratio,
            config.validation_ratio,
            config.test_ratio,
        ),
    )

    train_end = train_count
    validation_end = train_count + validation_count

    train = shuffled[:train_end]
    validation = shuffled[train_end:validation_end]
    test = shuffled[validation_end:]

    assert len(train) == train_count
    assert len(validation) == validation_count
    assert len(test) == test_count

    return train, validation, test


def split_dataset(
    records: list[Any] | tuple[Any, ...],
    config: SplitConfig | None = None,
) -> DatasetSplit:
    config = config or SplitConfig()
    config.validate()

    records = list(records)

    if not records:
        statistics = SplitStatistics(
            total_rows=0,
            train_rows=0,
            validation_rows=0,
            test_rows=0,
        )

        return DatasetSplit(
            train=(),
            validation=(),
            test=(),
            statistics=statistics,
        )

    rng = random.Random(config.seed)

    if config.stratify_by is None:
        train, validation, test = _split_group(
            records,
            config,
            rng,
        )

    else:
        groups: dict[str, list[Any]] = defaultdict(list)

        for record in records:
            value = get_field(
                record,
                config.stratify_by,
            )

            if value is None:
                raise ValueError(
                    f"Record is missing stratification field "
                    f"'{config.stratify_by}'."
                )

            groups[str(value)].append(record)

        train = []
        validation = []
        test = []

        for group_records in groups.values():
            group_train, group_validation, group_test = _split_group(
                group_records,
                config,
                rng,
            )

            train.extend(group_train)
            validation.extend(group_validation)
            test.extend(group_test)

        rng.shuffle(train)
        rng.shuffle(validation)
        rng.shuffle(test)

        # Stratified rounding can leave the global totals different
        # from the exact requested ratios. Rebalance the boundaries
        # without introducing duplicates or losing records.
        target_train, target_validation, target_test = _allocate_counts(
            len(records),
            (
                config.train_ratio,
                config.validation_ratio,
                config.test_ratio,
            ),
        )

        while len(train) > target_train:
            if len(validation) < target_validation:
                validation.append(train.pop())
            else:
                test.append(train.pop())

        while len(train) < target_train:
            if len(validation) > target_validation:
                train.append(validation.pop())
            elif len(test) > target_test:
                train.append(test.pop())
            else:
                break

        while len(validation) > target_validation:
            if len(test) < target_test:
                test.append(validation.pop())
            else:
                train.append(validation.pop())

        while len(validation) < target_validation:
            if len(test) > target_test:
                validation.append(test.pop())
            elif len(train) > target_train:
                validation.append(train.pop())
            else:
                break

        while len(test) > target_test:
            if len(train) < target_train:
                train.append(test.pop())
            else:
                validation.append(test.pop())

        while len(test) < target_test:
            if len(train) > target_train:
                test.append(train.pop())
            elif len(validation) > target_validation:
                test.append(validation.pop())
            else:
                break

        rng.shuffle(train)
        rng.shuffle(validation)
        rng.shuffle(test)

    statistics = SplitStatistics(
        total_rows=len(records),
        train_rows=len(train),
        validation_rows=len(validation),
        test_rows=len(test),
    )

    assert (
        len(train)
        + len(validation)
        + len(test)
        == len(records)
    )

    return DatasetSplit(
        train=tuple(train),
        validation=tuple(validation),
        test=tuple(test),
        statistics=statistics,
    )
