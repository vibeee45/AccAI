from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "all-MiniLM-L6-v2"
    normalize_embeddings: bool = True
    batch_size: int = 32
    max_length: int = 256

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("model_name cannot be empty.")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        if self.max_length <= 0:
            raise ValueError("max_length must be greater than zero.")

        if not isinstance(self.normalize_embeddings, bool):
            raise TypeError("normalize_embeddings must be a boolean.")
