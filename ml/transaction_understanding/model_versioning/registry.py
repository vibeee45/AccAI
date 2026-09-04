from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .schemas import (
    ModelMetrics,
    ModelVersion,
)


class ModelRegistry:
    def __init__(
        self,
        registry_path: str | Path,
    ) -> None:
        self.registry_path = Path(
            registry_path
        )

        self.registry_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _file_path(
        self,
        model_name: str,
    ) -> Path:
        safe_name = (
            model_name
            .strip()
            .replace(" ", "_")
        )

        return self.registry_path / (
            f"{safe_name}.json"
        )

    def save(
        self,
        model_version: ModelVersion,
    ) -> None:
        path = self._file_path(
            model_version.model_name
        )

        versions = []

        if path.exists():
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                versions = json.load(file)

        serialized = asdict(
            model_version
        )

        serialized["created_at"] = (
            model_version.created_at.isoformat()
        )

        versions = [
            version
            for version in versions
            if not (
                version["version"]
                == model_version.version
            )
        ]

        versions.append(serialized)

        versions.sort(
            key=lambda item: item["version"]
        )

        temporary_path = path.with_suffix(
            ".tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                versions,
                file,
                indent=2,
                sort_keys=True,
            )

        temporary_path.replace(path)

    def load(
        self,
        model_name: str,
        version: str,
    ) -> ModelVersion:
        path = self._file_path(
            model_name
        )

        if not path.exists():
            raise FileNotFoundError(
                f"No registry found for model "
                f"'{model_name}'."
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            versions = json.load(file)

        for item in versions:
            if item["version"] == version:
                return self._deserialize(
                    item
                )

        raise KeyError(
            f"Model version '{version}' "
            f"was not found for "
            f"'{model_name}'."
        )

    def list_versions(
        self,
        model_name: str,
    ) -> list[ModelVersion]:
        path = self._file_path(
            model_name
        )

        if not path.exists():
            return []

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            versions = json.load(file)

        return [
            self._deserialize(version)
            for version in versions
        ]

    def latest(
        self,
        model_name: str,
    ) -> ModelVersion:
        versions = self.list_versions(
            model_name
        )

        if not versions:
            raise KeyError(
                f"No versions found for "
                f"'{model_name}'."
            )

        return versions[-1]

    @staticmethod
    def _deserialize(
        item: dict,
    ) -> ModelVersion:
        metrics = ModelMetrics(
            **item.get(
                "metrics",
                {},
            )
        )

        return ModelVersion(
            model_name=item["model_name"],
            version=item["version"],
            algorithm=item["algorithm"],
            dataset_version=item[
                "dataset_version"
            ],
            model_path=item["model_path"],
            checksum=item["checksum"],
            created_at=datetime.fromisoformat(
                item["created_at"]
            ),
            parameters=item.get(
                "parameters",
                {},
            ),
            metrics=metrics,
        )
