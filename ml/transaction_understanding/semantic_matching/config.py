from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticMatchingConfig:
    similarity_threshold: float = 0.70
    top_k: int = 5

    def __post_init__(self) -> None:
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(
                "similarity_threshold must be between 0 and 1."
            )

        if self.top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )
