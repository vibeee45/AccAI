from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeduplicationConfig:
    remove_exact_duplicates: bool = True
    remove_identical_fingerprints: bool = False

    def validate(self) -> None:
        if not isinstance(self.remove_exact_duplicates, bool):
            raise ValueError(
                "remove_exact_duplicates must be boolean"
            )

        if not isinstance(self.remove_identical_fingerprints, bool):
            raise ValueError(
                "remove_identical_fingerprints must be boolean"
            )


@dataclass(frozen=True)
class DuplicateRecord:
    row_index: int
    duplicate_of: int
    fingerprint: str
    duplicate_type: str = "exact"


@dataclass(frozen=True)
class DeduplicationStats:
    rows_input: int
    rows_output: int
    exact_duplicates_removed: int
    fingerprint_duplicates_removed: int
    semantic_duplicates_detected: int = 0

    @property
    def duplicates_removed(self) -> int:
        return (
            self.exact_duplicates_removed
            + self.fingerprint_duplicates_removed
        )

    @property
    def duplicate_rate(self) -> float:
        if self.rows_input == 0:
            return 0.0

        return self.duplicates_removed / self.rows_input


@dataclass(frozen=True)
class DeduplicationResult:
    records: tuple
    duplicates: tuple[DuplicateRecord, ...]
    stats: DeduplicationStats
