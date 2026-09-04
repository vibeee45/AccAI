from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .config import ModelVersioningConfig
from .registry import ModelRegistry
from .schemas import (
    ModelMetrics,
    ModelVersion,
)


class ModelVersioner:
    def __init__(
        self,
        config: ModelVersioningConfig | None = None,
    ) -> None:
        self.config = (
            config
            or ModelVersioningConfig()
        )

        self.registry = ModelRegistry(
            self.config.registry_path
        )

    def calculate_checksum(
        self,
        model_path: str | Path,
    ) -> str:
        path = Path(model_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                "model_path must point to a file."
            )

        hasher = hashlib.sha256()

        with path.open(
            "rb"
        ) as file:
            while chunk := file.read(
                1024 * 1024
            ):
                hasher.update(chunk)

        return hasher.hexdigest()

    def create_version(
        self,
        model_name: str,
        version: str,
        algorithm: str,
        dataset_version: str,
        model_path: str | Path,
        parameters: dict[str, object] | None = None,
        metrics: ModelMetrics | None = None,
    ) -> ModelVersion:
        checksum = self.calculate_checksum(
            model_path
        )

        return ModelVersion(
            model_name=model_name,
            version=version,
            algorithm=algorithm,
            dataset_version=dataset_version,
            model_path=str(
                Path(model_path)
            ),
            checksum=checksum,
            created_at=datetime.now(
                timezone.utc
            ),
            parameters=parameters or {},
            metrics=metrics
            or ModelMetrics(),
        )

    def register(
        self,
        model_version: ModelVersion,
    ) -> ModelVersion:
        self.registry.save(
            model_version
        )

        return model_version

    def register_model(
        self,
        model_name: str,
        version: str,
        algorithm: str,
        dataset_version: str,
        model_path: str | Path,
        parameters: dict[str, object] | None = None,
        metrics: ModelMetrics | None = None,
    ) -> ModelVersion:
        model_version = self.create_version(
            model_name=model_name,
            version=version,
            algorithm=algorithm,
            dataset_version=dataset_version,
            model_path=model_path,
            parameters=parameters,
            metrics=metrics,
        )

        return self.register(
            model_version
        )

    def get_version(
        self,
        model_name: str,
        version: str,
    ) -> ModelVersion:
        return self.registry.load(
            model_name,
            version,
        )

    def get_latest(
        self,
        model_name: str,
    ) -> ModelVersion:
        return self.registry.latest(
            model_name
        )

    def list_versions(
        self,
        model_name: str,
    ) -> list[ModelVersion]:
        return self.registry.list_versions(
            model_name
        )

    def verify_checksum(
        self,
        model_version: ModelVersion,
    ) -> bool:
        current_checksum = (
            self.calculate_checksum(
                model_version.model_path
            )
        )

        return (
            current_checksum
            == model_version.checksum
        )

    def is_ready(self) -> bool:
        return True
