from __future__ import annotations

from typing import Any

from .fingerprints import (
    record_fingerprint,
    semantic_fingerprint,
)
from .schemas import (
    DeduplicationConfig,
    DeduplicationResult,
    DeduplicationStats,
    DuplicateRecord,
)


def deduplicate_records(
    records: list[Any] | tuple[Any, ...],
    config: DeduplicationConfig | None = None,
) -> DeduplicationResult:
    config = config or DeduplicationConfig()
    config.validate()

    output = []
    duplicates = []

    exact_seen: dict[str, int] = {}
    semantic_seen: dict[str, int] = {}

    exact_removed = 0
    fingerprint_removed = 0
    semantic_detected = 0

    for row_index, record in enumerate(records):
        fingerprint = record_fingerprint(record)
        semantic = semantic_fingerprint(record)

        if (
            config.remove_exact_duplicates
            and fingerprint in exact_seen
        ):
            duplicates.append(
                DuplicateRecord(
                    row_index=row_index,
                    duplicate_of=exact_seen[fingerprint],
                    fingerprint=fingerprint,
                    duplicate_type="exact",
                )
            )

            exact_removed += 1
            continue

        if semantic in semantic_seen:
            semantic_detected += 1

        if (
            config.remove_identical_fingerprints
            and semantic in semantic_seen
        ):
            duplicates.append(
                DuplicateRecord(
                    row_index=row_index,
                    duplicate_of=semantic_seen[semantic],
                    fingerprint=fingerprint,
                    duplicate_type="semantic",
                )
            )

            fingerprint_removed += 1
            continue

        exact_seen[fingerprint] = row_index
        semantic_seen.setdefault(semantic, row_index)

        output.append(record)

    stats = DeduplicationStats(
        rows_input=len(records),
        rows_output=len(output),
        exact_duplicates_removed=exact_removed,
        fingerprint_duplicates_removed=fingerprint_removed,
        semantic_duplicates_detected=semantic_detected,
    )

    return DeduplicationResult(
        records=tuple(output),
        duplicates=tuple(duplicates),
        stats=stats,
    )
