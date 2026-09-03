from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SourceType(str, Enum):
    """Supported public dataset source types."""

    KAGGLE = "kaggle"
    GITHUB = "github"
    DIRECT = "direct"


@dataclass(frozen=True)
class DatasetSource:
    """
    Metadata describing a public dataset source.

    This object contains source information only.
    It does not download or transform dataset contents.
    """

    source_id: str
    name: str
    source_type: SourceType
    url: str
    description: str
    license: str
    expected_format: str
    destination: str
    enabled: bool = True


PUBLIC_DATASETS: tuple[DatasetSource, ...] = (
    DatasetSource(
        source_id="kaggle_accounting_transactions",
        name="AccountingTransactions",
        source_type=SourceType.KAGGLE,
        url="https://www.kaggle.com/datasets/datamonstereeeeee/accountingtransactions",
        description=(
            "Accounting transaction text dataset classified into "
            "Assets, Liabilities, Revenue, Expense and Equity."
        ),
        license="Unknown",
        expected_format="CSV",
        destination="ml/data/raw/public/accounting_transactions",
    ),
    DatasetSource(
        source_id="kaggle_accountancy",
        name="Accountancy",
        source_type=SourceType.KAGGLE,
        url="https://www.kaggle.com/datasets/premishan/accountancy",
        description=(
            "Financial transaction data represented as double-entry "
            "journal records."
        ),
        license="Unknown",
        expected_format="CSV",
        destination="ml/data/raw/public/accountancy",
    ),
    DatasetSource(
        source_id="github_synthetic_accounting_generator",
        name="Synthetic Accounting Data Generator",
        source_type=SourceType.GITHUB,
        url="https://github.com/R3n0va/synthetic-accounting-data-generator",
        description=(
            "Reference implementation for deterministic synthetic "
            "accounting data generation and validation."
        ),
        license="MIT",
        expected_format="CSV/JSON",
        destination="ml/data/raw/public/synthetic_accounting_reference",
        enabled=False,
    ),
)


def get_public_datasets() -> tuple[DatasetSource, ...]:
    """Return all registered public dataset sources."""

    return PUBLIC_DATASETS


def get_enabled_datasets() -> tuple[DatasetSource, ...]:
    """Return only enabled public dataset sources."""

    return tuple(
        source
        for source in PUBLIC_DATASETS
        if source.enabled
    )


def get_dataset(source_id: str) -> DatasetSource | None:
    """Find a dataset source by its unique source ID."""

    normalized_id = source_id.strip()

    for source in PUBLIC_DATASETS:
        if source.source_id == normalized_id:
            return source

    return None


def validate_manifest() -> None:
    """
    Validate the public dataset registry.

    Raises:
        ValueError: If source metadata is invalid or duplicated.
    """

    source_ids = set()

    for source in PUBLIC_DATASETS:
        if not source.source_id.strip():
            raise ValueError("Dataset source ID cannot be empty.")

        if source.source_id in source_ids:
            raise ValueError(
                f"Duplicate dataset source ID: {source.source_id}"
            )

        source_ids.add(source.source_id)

        if not source.name.strip():
            raise ValueError(
                f"Dataset name cannot be empty: {source.source_id}"
            )

        if not source.url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid dataset URL: {source.source_id}"
            )

        if not source.description.strip():
            raise ValueError(
                f"Dataset description cannot be empty: {source.source_id}"
            )

        if not source.license.strip():
            raise ValueError(
                f"Dataset license cannot be empty: {source.source_id}"
            )

        if not source.expected_format.strip():
            raise ValueError(
                f"Expected format cannot be empty: {source.source_id}"
            )

        if not source.destination.strip():
            raise ValueError(
                f"Destination cannot be empty: {source.source_id}"
            )


def ensure_destination_directories(root: Path) -> None:
    """
    Create destination directories for enabled datasets.

    Existing directories are left untouched.
    """

    for source in get_enabled_datasets():
        destination = root / source.destination
        destination.mkdir(parents=True, exist_ok=True)