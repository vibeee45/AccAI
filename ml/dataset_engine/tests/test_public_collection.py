from pathlib import Path

import pytest

from ml.dataset_engine.sources import (
    CollectedDataset,
    DatasetCollectionError,
    DatasetSource,
    SourceType,
    calculate_sha256,
    collect_local_file,
    get_dataset,
    get_enabled_datasets,
    get_public_datasets,
    validate_collected_dataset,
    validate_manifest,
)


# ---------------------------------------------------------------------------
# Manifest tests
# ---------------------------------------------------------------------------

def test_public_dataset_manifest_is_valid():
    """The complete public dataset registry should pass validation."""

    validate_manifest()


def test_public_dataset_manifest_is_not_empty():
    """At least one public dataset should be registered."""

    datasets = get_public_datasets()

    assert len(datasets) >= 1


def test_public_dataset_ids_are_unique():
    """Every registered dataset must have a unique source ID."""

    datasets = get_public_datasets()

    source_ids = [
        dataset.source_id
        for dataset in datasets
    ]

    assert len(source_ids) == len(set(source_ids))


def test_public_dataset_names_are_not_empty():
    """Every registered dataset must have a name."""

    for dataset in get_public_datasets():
        assert dataset.name.strip()


def test_manifest_contains_valid_urls():
    """Every registered source must contain an HTTP(S) URL."""

    for dataset in get_public_datasets():
        assert dataset.url.startswith(
            ("http://", "https://")
        )


def test_manifest_contains_descriptions():
    """Every dataset should document its purpose."""

    for dataset in get_public_datasets():
        assert dataset.description.strip()


def test_manifest_contains_licenses():
    """Every dataset must have license metadata."""

    for dataset in get_public_datasets():
        assert dataset.license.strip()


def test_manifest_contains_expected_formats():
    """Every dataset must declare its expected file format."""

    for dataset in get_public_datasets():
        assert dataset.expected_format.strip()


def test_manifest_contains_destinations():
    """Every dataset must define a raw-data destination."""

    for dataset in get_public_datasets():
        assert dataset.destination.strip()


# ---------------------------------------------------------------------------
# Dataset lookup tests
# ---------------------------------------------------------------------------

def test_get_dataset_by_id():
    """A registered dataset should be retrievable by source ID."""

    dataset = get_dataset(
        "kaggle_accounting_transactions"
    )

    assert dataset is not None
    assert dataset.source_id == "kaggle_accounting_transactions"
    assert dataset.name == "AccountingTransactions"
    assert dataset.source_type == SourceType.KAGGLE


def test_get_dataset_ignores_surrounding_whitespace():
    """Dataset lookup should tolerate surrounding whitespace."""

    dataset = get_dataset(
        "  kaggle_accounting_transactions  "
    )

    assert dataset is not None
    assert dataset.source_id == "kaggle_accounting_transactions"


def test_unknown_dataset_returns_none():
    """Unknown dataset IDs should return None."""

    assert get_dataset("does_not_exist") is None


def test_empty_dataset_id_returns_none():
    """An empty dataset ID should not match any source."""

    assert get_dataset("") is None


# ---------------------------------------------------------------------------
# Enabled dataset tests
# ---------------------------------------------------------------------------

def test_enabled_dataset_sources_exist():
    """Enabled dataset collection should return registered sources."""

    datasets = get_enabled_datasets()

    assert len(datasets) >= 1

    for dataset in datasets:
        assert dataset.enabled is True


def test_disabled_dataset_is_not_returned_as_enabled():
    """Disabled sources should not appear in the enabled collection."""

    all_datasets = get_public_datasets()
    enabled_datasets = get_enabled_datasets()

    enabled_ids = {
        dataset.source_id
        for dataset in enabled_datasets
    }

    for dataset in all_datasets:
        if not dataset.enabled:
            assert dataset.source_id not in enabled_ids


# ---------------------------------------------------------------------------
# DatasetSource tests
# ---------------------------------------------------------------------------

def test_dataset_source_stores_metadata():
    """DatasetSource should preserve all supplied metadata."""

    source = DatasetSource(
        source_id="test_dataset",
        name="Test Dataset",
        source_type=SourceType.DIRECT,
        url="https://example.com/dataset.csv",
        description="Test accounting dataset",
        license="MIT",
        expected_format="CSV",
        destination="ml/data/raw/public/test_dataset",
        enabled=True,
    )

    assert source.source_id == "test_dataset"
    assert source.name == "Test Dataset"
    assert source.source_type == SourceType.DIRECT
    assert source.url == "https://example.com/dataset.csv"
    assert source.description == "Test accounting dataset"
    assert source.license == "MIT"
    assert source.expected_format == "CSV"
    assert source.destination == (
        "ml/data/raw/public/test_dataset"
    )
    assert source.enabled is True


# ---------------------------------------------------------------------------
# SHA-256 tests
# ---------------------------------------------------------------------------

def test_sha256_is_deterministic(tmp_path: Path):
    """The same file should always produce the same SHA-256 hash."""

    file_path = tmp_path / "sample.txt"

    file_path.write_text(
        "ACCAI dataset engine",
        encoding="utf-8",
    )

    first_hash = calculate_sha256(file_path)
    second_hash = calculate_sha256(file_path)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_sha256_changes_when_file_changes(tmp_path: Path):
    """Changing file contents should change its SHA-256 hash."""

    file_path = tmp_path / "sample.txt"

    file_path.write_text(
        "ACCAI dataset engine",
        encoding="utf-8",
    )

    first_hash = calculate_sha256(file_path)

    file_path.write_text(
        "ACCAI dataset engine changed",
        encoding="utf-8",
    )

    second_hash = calculate_sha256(file_path)

    assert first_hash != second_hash


def test_sha256_missing_file_fails(tmp_path: Path):
    """Hashing a missing file should raise a collection error."""

    missing_file = tmp_path / "missing.txt"

    with pytest.raises(DatasetCollectionError):
        calculate_sha256(missing_file)


# ---------------------------------------------------------------------------
# Local dataset collection tests
# ---------------------------------------------------------------------------

def make_test_source() -> DatasetSource:
    """Create a reusable local test dataset source."""

    return DatasetSource(
        source_id="local_test",
        name="Local Test Dataset",
        source_type=SourceType.DIRECT,
        url="https://example.com/dataset.csv",
        description="Test accounting dataset",
        license="MIT",
        expected_format="CSV",
        destination="ml/data/raw/public/test",
    )


def test_collect_local_file(tmp_path: Path):
    """A valid local dataset should produce collection metadata."""

    file_path = tmp_path / "dataset.csv"

    file_path.write_text(
        "date,transaction,amount\n"
        "2026-01-01,Cash sale,1000\n",
        encoding="utf-8",
    )

    source = make_test_source()

    collected = collect_local_file(
        source,
        file_path,
    )

    assert isinstance(collected, CollectedDataset)
    assert collected.source_id == source.source_id
    assert collected.source_url == source.url
    assert collected.local_path == file_path
    assert collected.size_bytes == file_path.stat().st_size
    assert len(collected.sha256) == 64


def test_collect_local_file_does_not_modify_contents(
    tmp_path: Path,
):
    """Collection must preserve raw dataset contents exactly."""

    file_path = tmp_path / "dataset.csv"

    original_content = (
        "date,transaction,amount\n"
        "2026-01-01,Cash sale,1000\n"
    )

    file_path.write_text(
        original_content,
        encoding="utf-8",
    )

    source = make_test_source()

    collect_local_file(
        source,
        file_path,
    )

    assert file_path.read_text(
        encoding="utf-8"
    ) == original_content


def test_collect_missing_file_fails(tmp_path: Path):
    """Collecting a missing local file should fail."""

    source = make_test_source()

    with pytest.raises(DatasetCollectionError):
        collect_local_file(
            source,
            tmp_path / "missing.csv",
        )


# ---------------------------------------------------------------------------
# CollectedDataset validation tests
# ---------------------------------------------------------------------------

def test_validate_collected_dataset(tmp_path: Path):
    """Valid collected dataset metadata should pass validation."""

    file_path = tmp_path / "dataset.csv"

    file_path.write_text(
        "date,transaction,amount\n",
        encoding="utf-8",
    )

    source = make_test_source()

    collected = collect_local_file(
        source,
        file_path,
    )

    validate_collected_dataset(collected)


def test_invalid_collected_checksum_fails(tmp_path: Path):
    """An invalid SHA-256 checksum should fail validation."""

    file_path = tmp_path / "dataset.csv"

    file_path.write_text(
        "sample",
        encoding="utf-8",
    )

    collected = CollectedDataset(
        source_id="test",
        source_url="https://example.com/dataset.csv",
        local_path=file_path,
        sha256="invalid",
        size_bytes=file_path.stat().st_size,
    )

    with pytest.raises(DatasetCollectionError):
        validate_collected_dataset(collected)


def test_missing_collected_file_fails(tmp_path: Path):
    """Collected metadata pointing to a missing file should fail."""

    collected = CollectedDataset(
        source_id="test",
        source_url="https://example.com/dataset.csv",
        local_path=tmp_path / "missing.csv",
        sha256="a" * 64,
        size_bytes=0,
    )

    with pytest.raises(DatasetCollectionError):
        validate_collected_dataset(collected)


def test_empty_source_id_fails(tmp_path: Path):
    """Collected metadata requires a source ID."""

    file_path = tmp_path / "dataset.csv"
    file_path.write_text("sample", encoding="utf-8")

    collected = CollectedDataset(
        source_id="",
        source_url="https://example.com/dataset.csv",
        local_path=file_path,
        sha256="a" * 64,
        size_bytes=file_path.stat().st_size,
    )

    with pytest.raises(DatasetCollectionError):
        validate_collected_dataset(collected)


def test_invalid_source_url_fails(tmp_path: Path):
    """Collected metadata requires an HTTP(S) source URL."""

    file_path = tmp_path / "dataset.csv"
    file_path.write_text("sample", encoding="utf-8")

    collected = CollectedDataset(
        source_id="test",
        source_url="invalid-url",
        local_path=file_path,
        sha256="a" * 64,
        size_bytes=file_path.stat().st_size,
    )

    with pytest.raises(DatasetCollectionError):
        validate_collected_dataset(collected)


def test_negative_dataset_size_fails(tmp_path: Path):
    """Dataset size cannot be negative."""

    file_path = tmp_path / "dataset.csv"
    file_path.write_text("sample", encoding="utf-8")

    collected = CollectedDataset(
        source_id="test",
        source_url="https://example.com/dataset.csv",
        local_path=file_path,
        sha256="a" * 64,
        size_bytes=-1,
    )

    with pytest.raises(DatasetCollectionError):
        validate_collected_dataset(collected)


def test_short_checksum_fails(tmp_path: Path):
    """Checksum must contain a valid SHA-256 length."""

    file_path = tmp_path / "dataset.csv"
    file_path.write_text("sample", encoding="utf-8")

    collected = CollectedDataset(
        source_id="test",
        source_url="https://example.com/dataset.csv",
        local_path=file_path,
        sha256="abc",
        size_bytes=file_path.stat().st_size,
    )

    with pytest.raises(DatasetCollectionError):
        validate_collected_dataset(collected)


# ---------------------------------------------------------------------------
# Collector behavior tests
# ---------------------------------------------------------------------------

def test_download_invalid_url_fails(tmp_path: Path):
    """The downloader should reject unsupported URL schemes."""

    from ml.dataset_engine.sources import download_file

    destination = tmp_path / "dataset.csv"

    with pytest.raises(DatasetCollectionError):
        download_file(
            "ftp://example.com/dataset.csv",
            destination,
        )


def test_download_existing_file_without_overwrite_fails(
    tmp_path: Path,
):
    """Existing files must not be overwritten by default."""

    from ml.dataset_engine.sources import download_file

    destination = tmp_path / "dataset.csv"

    destination.write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(DatasetCollectionError):
        download_file(
            "https://example.com/dataset.csv",
            destination,
        )

    assert destination.read_text(
        encoding="utf-8"
    ) == "existing"