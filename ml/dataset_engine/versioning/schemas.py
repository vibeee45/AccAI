from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DatasetVersionConfig:
    dataset_name: str
    version: str
    seed: int
    source: str
    description: str = ""

    def validate(self) -> None:
        if not self.dataset_name.strip():
            raise ValueError("dataset_name cannot be empty.")

        if not self.version.strip():
            raise ValueError("version cannot be empty.")

        if not self.source.strip():
            raise ValueError("source cannot be empty.")

        if not isinstance(self.seed, int):
            raise ValueError("seed must be an integer.")


@dataclass(frozen=True)
class DatasetVersion:
    dataset_name: str
    version: str
    seed: int
    source: str
    description: str
    created_at: datetime

    total_rows: int
    train_rows: int
    validation_rows: int
    test_rows: int

    checksum: str

    @property
    def version_id(self) -> str:
        return f"{self.dataset_name}-{self.version}"


@dataclass(frozen=True)
class DatasetManifest:
    version_id: str
    dataset_name: str
    version: str
    seed: int
    source: str
    description: str
    created_at: str
    total_rows: int
    train_rows: int
    validation_rows: int
    test_rows: int
    checksum: str
