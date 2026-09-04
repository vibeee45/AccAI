from datetime import datetime, timezone

import pytest

from ml.transaction_understanding.model_versioning.config import (
    ModelVersioningConfig,
)
from ml.transaction_understanding.model_versioning.inference import (
    ModelVersioningService,
)
from ml.transaction_understanding.model_versioning.registry import (
    ModelRegistry,
)
from ml.transaction_understanding.model_versioning.schemas import (
    ModelMetrics,
    ModelRegistryEntry,
    ModelVersion,
)
from ml.transaction_understanding.model_versioning.versioner import (
    ModelVersioner,
)


def create_model_file(tmp_path, content=b"test model"):
    path = tmp_path / "model.bin"
    path.write_bytes(content)
    return path


def test_default_config():
    config = ModelVersioningConfig()

    assert config.registry_path == "ml/model_registry"
    assert config.hash_algorithm == "sha256"


def test_custom_config(tmp_path):
    config = ModelVersioningConfig(
        registry_path=str(tmp_path),
        hash_algorithm="sha256",
    )

    assert config.registry_path == str(tmp_path)
    assert config.hash_algorithm == "sha256"


def test_config_rejects_empty_registry_path():
    with pytest.raises(ValueError):
        ModelVersioningConfig(
            registry_path=""
        )


def test_config_rejects_unsupported_hash():
    with pytest.raises(ValueError):
        ModelVersioningConfig(
            hash_algorithm="md5"
        )


def test_registry_directory_property(tmp_path):
    config = ModelVersioningConfig(
        registry_path=str(tmp_path)
    )

    assert config.registry_directory == tmp_path


def test_model_metrics():
    metrics = ModelMetrics(
        accuracy=0.95,
        precision=0.94,
        recall=0.93,
        f1=0.935,
    )

    assert metrics.accuracy == 0.95
    assert metrics.f1 == 0.935


def test_model_metrics_allow_empty():
    metrics = ModelMetrics()

    assert metrics.accuracy is None
    assert metrics.f1 is None


def test_model_metrics_reject_invalid_accuracy():
    with pytest.raises(ValueError):
        ModelMetrics(
            accuracy=1.2
        )


def test_model_metrics_reject_negative_precision():
    with pytest.raises(ValueError):
        ModelMetrics(
            precision=-0.1
        )


def test_model_version():
    version = ModelVersion(
        model_name="transaction_classifier",
        version="1.0.0",
        algorithm="logistic_regression",
        dataset_version="dataset-1.0.0",
        model_path="model.bin",
        checksum="abc123",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    assert version.model_name == (
        "transaction_classifier"
    )
    assert version.version == "1.0.0"


def test_model_version_with_parameters():
    version = ModelVersion(
        model_name="classifier",
        version="1.0.0",
        algorithm="logistic_regression",
        dataset_version="dataset-1.0.0",
        model_path="model.bin",
        checksum="abc123",
        created_at=datetime.now(
            timezone.utc
        ),
        parameters={
            "C": 1.0,
            "max_iter": 1000,
        },
    )

    assert version.parameters["C"] == 1.0


def test_model_version_rejects_empty_model_name():
    with pytest.raises(ValueError):
        ModelVersion(
            model_name="",
            version="1.0",
            algorithm="test",
            dataset_version="dataset",
            model_path="model.bin",
            checksum="abc",
            created_at=datetime.now(
                timezone.utc
            ),
        )


def test_model_version_rejects_empty_version():
    with pytest.raises(ValueError):
        ModelVersion(
            model_name="model",
            version="",
            algorithm="test",
            dataset_version="dataset",
            model_path="model.bin",
            checksum="abc",
            created_at=datetime.now(
                timezone.utc
            ),
        )


def test_model_version_rejects_invalid_datetime():
    with pytest.raises(TypeError):
        ModelVersion(
            model_name="model",
            version="1.0",
            algorithm="test",
            dataset_version="dataset",
            model_path="model.bin",
            checksum="abc",
            created_at="2026-01-01",
        )


def test_model_registry_entry():
    version = ModelVersion(
        model_name="classifier",
        version="1.0.0",
        algorithm="test",
        dataset_version="dataset-1",
        model_path="model.bin",
        checksum="abc",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    entry = ModelRegistryEntry(
        model_name="classifier",
        versions=[version],
    )

    assert entry.model_name == "classifier"
    assert len(entry.versions) == 1


def test_registry_creates_directory(tmp_path):
    registry_path = (
        tmp_path / "registry"
    )

    ModelRegistry(registry_path)

    assert registry_path.exists()


def test_checksum(tmp_path):
    model_path = create_model_file(
        tmp_path,
        b"hello world",
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    checksum = versioner.calculate_checksum(
        model_path
    )

    assert len(checksum) == 64


def test_checksum_is_deterministic(tmp_path):
    model_path = create_model_file(
        tmp_path,
        b"hello world",
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    first = versioner.calculate_checksum(
        model_path
    )

    second = versioner.calculate_checksum(
        model_path
    )

    assert first == second


def test_different_content_has_different_checksum(
    tmp_path,
):
    first_path = create_model_file(
        tmp_path,
        b"model one",
    )

    second_path = (
        tmp_path / "model_two.bin"
    )

    second_path.write_bytes(
        b"model two"
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    first = versioner.calculate_checksum(
        first_path
    )

    second = versioner.calculate_checksum(
        second_path
    )

    assert first != second


def test_checksum_missing_file(tmp_path):
    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    with pytest.raises(FileNotFoundError):
        versioner.calculate_checksum(
            tmp_path / "missing.bin"
        )


def test_checksum_rejects_directory(tmp_path):
    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    with pytest.raises(ValueError):
        versioner.calculate_checksum(
            tmp_path
        )


def test_create_version(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    version = versioner.create_version(
        model_name="transaction_classifier",
        version="1.0.0",
        algorithm="logistic_regression",
        dataset_version="dataset-1.0.0",
        model_path=model_path,
    )

    assert version.model_name == (
        "transaction_classifier"
    )
    assert version.version == "1.0.0"
    assert version.checksum


def test_create_version_with_metrics(
    tmp_path,
):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    metrics = ModelMetrics(
        accuracy=0.95,
        f1=0.94,
    )

    version = versioner.create_version(
        model_name="classifier",
        version="1.0.0",
        algorithm="test",
        dataset_version="dataset-1",
        model_path=model_path,
        metrics=metrics,
    )

    assert version.metrics.accuracy == 0.95
    assert version.metrics.f1 == 0.94


def test_register_and_load(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    registry_path = (
        tmp_path / "registry"
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                registry_path
            )
        )
    )

    version = versioner.create_version(
        model_name="classifier",
        version="1.0.0",
        algorithm="test",
        dataset_version="dataset-1",
        model_path=model_path,
    )

    versioner.register(version)

    loaded = versioner.get_version(
        "classifier",
        "1.0.0",
    )

    assert loaded.model_name == (
        version.model_name
    )
    assert loaded.version == (
        version.version
    )
    assert loaded.checksum == (
        version.checksum
    )


def test_register_model(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    version = versioner.register_model(
        model_name="classifier",
        version="1.0.0",
        algorithm="test",
        dataset_version="dataset-1",
        model_path=model_path,
    )

    assert version.version == "1.0.0"


def test_list_versions(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    versioner.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    versioner.register_model(
        "classifier",
        "2.0.0",
        "test",
        "dataset-2",
        model_path,
    )

    versions = versioner.list_versions(
        "classifier"
    )

    assert len(versions) == 2
    assert versions[0].version == "1.0.0"
    assert versions[1].version == "2.0.0"


def test_latest_version(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    versioner.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    versioner.register_model(
        "classifier",
        "2.0.0",
        "test",
        "dataset-2",
        model_path,
    )

    latest = versioner.get_latest(
        "classifier"
    )

    assert latest.version == "2.0.0"


def test_get_missing_model(tmp_path):
    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    with pytest.raises(FileNotFoundError):
        versioner.get_version(
            "missing",
            "1.0.0",
        )


def test_get_missing_version(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    versioner.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    with pytest.raises(KeyError):
        versioner.get_version(
            "classifier",
            "9.0.0",
        )


def test_latest_missing_model(tmp_path):
    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    with pytest.raises(KeyError):
        versioner.get_latest(
            "missing"
        )


def test_list_missing_model_returns_empty(
    tmp_path,
):
    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    assert (
        versioner.list_versions(
            "missing"
        )
        == []
    )


def test_duplicate_version_is_replaced(
    tmp_path,
):
    model_path = create_model_file(
        tmp_path
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    versioner.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    versioner.register_model(
        "classifier",
        "1.0.0",
        "test-updated",
        "dataset-2",
        model_path,
    )

    versions = versioner.list_versions(
        "classifier"
    )

    assert len(versions) == 1
    assert versions[0].algorithm == (
        "test-updated"
    )


def test_checksum_verification(tmp_path):
    model_path = create_model_file(
        tmp_path,
        b"original model",
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    version = versioner.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    assert versioner.verify_checksum(
        version
    ) is True


def test_checksum_detects_modified_model(
    tmp_path,
):
    model_path = create_model_file(
        tmp_path,
        b"original model",
    )

    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    version = versioner.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    model_path.write_bytes(
        b"modified model"
    )

    assert versioner.verify_checksum(
        version
    ) is False


def test_registry_direct_save_load(
    tmp_path,
):
    registry = ModelRegistry(
        tmp_path / "registry"
    )

    version = ModelVersion(
        model_name="classifier",
        version="1.0.0",
        algorithm="test",
        dataset_version="dataset-1",
        model_path="model.bin",
        checksum="abc",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    registry.save(version)

    loaded = registry.load(
        "classifier",
        "1.0.0",
    )

    assert loaded.version == "1.0.0"


def test_registry_list_versions(
    tmp_path,
):
    registry = ModelRegistry(
        tmp_path / "registry"
    )

    version = ModelVersion(
        model_name="classifier",
        version="1.0.0",
        algorithm="test",
        dataset_version="dataset-1",
        model_path="model.bin",
        checksum="abc",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    registry.save(version)

    versions = registry.list_versions(
        "classifier"
    )

    assert len(versions) == 1


def test_registry_latest(
    tmp_path,
):
    registry = ModelRegistry(
        tmp_path / "registry"
    )

    for version_number in (
        "1.0.0",
        "2.0.0",
    ):
        registry.save(
            ModelVersion(
                model_name="classifier",
                version=version_number,
                algorithm="test",
                dataset_version="dataset",
                model_path="model.bin",
                checksum="abc",
                created_at=datetime.now(
                    timezone.utc
                ),
            )
        )

    assert (
        registry.latest(
            "classifier"
        ).version
        == "2.0.0"
    )


def test_service_checksum(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    checksum = service.calculate_checksum(
        model_path
    )

    assert len(checksum) == 64


def test_service_register(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    version = service.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    assert version.version == "1.0.0"


def test_service_get_version(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    service.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    version = service.get_version(
        "classifier",
        "1.0.0",
    )

    assert version.version == "1.0.0"


def test_service_latest(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    service.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    service.register_model(
        "classifier",
        "2.0.0",
        "test",
        "dataset-2",
        model_path,
    )

    assert (
        service.get_latest(
            "classifier"
        ).version
        == "2.0.0"
    )


def test_service_list_versions(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    service.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    assert len(
        service.list_versions(
            "classifier"
        )
    ) == 1


def test_service_verify_checksum(tmp_path):
    model_path = create_model_file(
        tmp_path
    )

    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    version = service.register_model(
        "classifier",
        "1.0.0",
        "test",
        "dataset-1",
        model_path,
    )

    assert service.verify_checksum(
        version
    ) is True


def test_versioner_ready(tmp_path):
    versioner = ModelVersioner(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    assert versioner.is_ready() is True


def test_service_ready(tmp_path):
    service = ModelVersioningService(
        ModelVersioningConfig(
            registry_path=str(
                tmp_path / "registry"
            )
        )
    )

    assert service.is_ready() is True
