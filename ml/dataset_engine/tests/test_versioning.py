from pathlib import Path

import pytest

from ml.dataset_engine.generation import generate_transactions
from ml.dataset_engine.splitting import split_dataset
from ml.dataset_engine.versioning import (
    DatasetVersionConfig,
    calculate_dataset_checksum,
    create_dataset_version,
    create_manifest,
    load_manifest,
    save_manifest,
)


def make_split():
    records = generate_transactions(
        rows=100,
        seed=42,
    )

    return split_dataset(records)


def test_version_config():
    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    config.validate()


def test_empty_dataset_name_rejected():
    config = DatasetVersionConfig(
        dataset_name="",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_empty_version_rejected():
    config = DatasetVersionConfig(
        dataset_name="accai",
        version="",
        seed=42,
        source="synthetic",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_empty_source_rejected():
    config = DatasetVersionConfig(
        dataset_name="accai",
        version="v1.0.0",
        seed=42,
        source="",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_seed_must_be_integer():
    config = DatasetVersionConfig(
        dataset_name="accai",
        version="v1.0.0",
        seed="42",
        source="synthetic",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_checksum_is_deterministic():
    records = generate_transactions(
        rows=50,
        seed=42,
    )

    first = calculate_dataset_checksum(records)
    second = calculate_dataset_checksum(records)

    assert first == second
    assert len(first) == 64


def test_different_data_changes_checksum():
    first = generate_transactions(
        rows=50,
        seed=42,
    )

    second = generate_transactions(
        rows=50,
        seed=99,
    )

    assert (
        calculate_dataset_checksum(first)
        != calculate_dataset_checksum(second)
    )


def test_create_dataset_version():
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
        description="Initial ACCAI dataset.",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    assert version.dataset_name == "accai_transactions"
    assert version.version == "v1.0.0"
    assert version.seed == 42
    assert version.source == "synthetic"
    assert version.total_rows == 100
    assert version.train_rows == len(split.train)
    assert version.validation_rows == len(split.validation)
    assert version.test_rows == len(split.test)
    assert len(version.checksum) == 64


def test_version_id():
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    assert version.version_id == "accai_transactions-v1.0.0"


def test_manifest_creation():
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    manifest = create_manifest(version)

    assert manifest.version_id == version.version_id
    assert manifest.checksum == version.checksum
    assert manifest.total_rows == version.total_rows


def test_manifest_save_and_load(tmp_path: Path):
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    manifest = create_manifest(version)

    path = tmp_path / "manifest.json"

    save_manifest(manifest, path)

    loaded = load_manifest(path)

    assert loaded == manifest


def test_manifest_file_exists(tmp_path: Path):
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    manifest = create_manifest(version)

    path = save_manifest(
        manifest,
        tmp_path / "dataset" / "manifest.json",
    )

    assert path.exists()


def test_manifest_is_valid_json(tmp_path: Path):
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    manifest = create_manifest(version)

    path = save_manifest(
        manifest,
        tmp_path / "manifest.json",
    )

    loaded = load_manifest(path)

    assert loaded.dataset_name == "accai_transactions"


def test_total_rows_match_splits():
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai_transactions",
        version="v1.0.0",
        seed=42,
        source="synthetic",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    assert (
        version.train_rows
        + version.validation_rows
        + version.test_rows
        == version.total_rows
    )


def test_description_is_preserved():
    split = make_split()

    config = DatasetVersionConfig(
        dataset_name="accai",
        version="v1.0.0",
        seed=42,
        source="synthetic",
        description="Test dataset",
    )

    version = create_dataset_version(
        config,
        split.train,
        split.validation,
        split.test,
    )

    assert version.description == "Test dataset"


def test_checksum_changes_when_record_order_changes():
    records = generate_transactions(
        rows=10,
        seed=42,
    )

    first = calculate_dataset_checksum(records)
    second = calculate_dataset_checksum(
        tuple(reversed(records))
    )

    assert first != second
