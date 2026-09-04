from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ModelMetrics:
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None

    def __post_init__(self) -> None:
        values = (
            self.accuracy,
            self.precision,
            self.recall,
            self.f1,
        )

        for value in values:
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(
                    "Model metrics must be between 0 and 1."
                )


@dataclass(frozen=True)
class ModelVersion:
    model_name: str
    version: str
    algorithm: str
    dataset_version: str
    model_path: str
    checksum: str
    created_at: datetime
    parameters: dict[str, object] = field(
        default_factory=dict
    )
    metrics: ModelMetrics = field(
        default_factory=ModelMetrics
    )

    def __post_init__(self) -> None:
        required_fields = (
            ("model_name", self.model_name),
            ("version", self.version),
            ("algorithm", self.algorithm),
            ("dataset_version", self.dataset_version),
            ("model_path", self.model_path),
            ("checksum", self.checksum),
        )

        for name, value in required_fields:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{name} cannot be empty."
                )

        if not isinstance(
            self.created_at,
            datetime,
        ):
            raise TypeError(
                "created_at must be a datetime."
            )

        if not isinstance(
            self.parameters,
            dict,
        ):
            raise TypeError(
                "parameters must be a dictionary."
            )

        if not isinstance(
            self.metrics,
            ModelMetrics,
        ):
            raise TypeError(
                "metrics must be ModelMetrics."
            )


@dataclass(frozen=True)
class ModelRegistryEntry:
    model_name: str
    versions: list[ModelVersion]

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError(
                "model_name cannot be empty."
            )

        if not isinstance(
            self.versions,
            list,
        ):
            raise TypeError(
                "versions must be a list."
            )
