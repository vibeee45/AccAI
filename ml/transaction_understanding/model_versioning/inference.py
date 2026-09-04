from __future__ import annotations

from pathlib import Path

from .config import ModelVersioningConfig
from .schemas import ModelMetrics, ModelVersion
from .versioner import ModelVersioner


class ModelVersioningService:
    def __init__(
        self,
        config: ModelVersioningConfig | None = None,
    ) -> None:
        self.versioner = ModelVersioner(
            config
        )

    def calculate_checksum(
        self,
        model_path: str | Path,
    ) -> str:
        return self.versioner.calculate_checksum(
            model_path
        )

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
        return self.versioner.register_model(
            model_name=model_name,
            version=version,
            algorithm=algorithm,
            dataset_version=dataset_version,
            model_path=model_path,
            parameters=parameters,
            metrics=metrics,
        )

    def get_version(
        self,
        model_name: str,
        version: str,
    ) -> ModelVersion:
        return self.versioner.get_version(
            model_name,
            version,
        )

    def get_latest(
        self,
        model_name: str,
    ) -> ModelVersion:
        return self.versioner.get_latest(
            model_name
        )

    def list_versions(
        self,
        model_name: str,
    ) -> list[ModelVersion]:
        return self.versioner.list_versions(
            model_name
        )

    def verify_checksum(
        self,
        model_version: ModelVersion,
    ) -> bool:
        return self.versioner.verify_checksum(
            model_version
        )

    def is_ready(self) -> bool:
        return self.versioner.is_ready()
