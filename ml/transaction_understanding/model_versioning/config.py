from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelVersioningConfig:
    registry_path: str = "ml/model_registry"
    hash_algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if not self.registry_path.strip():
            raise ValueError(
                "registry_path cannot be empty."
            )

        if self.hash_algorithm.lower() != "sha256":
            raise ValueError(
                "Only sha256 is currently supported."
            )

    @property
    def registry_directory(self) -> Path:
        return Path(self.registry_path)
