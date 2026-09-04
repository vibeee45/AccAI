from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EmbeddingResult:
    text: str
    vector: np.ndarray
    dimension: int

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")

        if not self.text.strip():
            raise ValueError("text cannot be empty.")

        if not isinstance(self.vector, np.ndarray):
            raise TypeError("vector must be a numpy.ndarray.")

        if self.vector.ndim != 1:
            raise ValueError("vector must be one-dimensional.")

        if self.dimension <= 0:
            raise ValueError("dimension must be greater than zero.")

        if len(self.vector) != self.dimension:
            raise ValueError(
                "dimension must match the vector length."
            )


@dataclass(frozen=True)
class BatchEmbeddingResult:
    texts: list[str]
    vectors: np.ndarray
    dimension: int

    def __post_init__(self) -> None:
        if not self.texts:
            raise ValueError("texts cannot be empty.")

        if not isinstance(self.vectors, np.ndarray):
            raise TypeError("vectors must be a numpy.ndarray.")

        if self.vectors.ndim != 2:
            raise ValueError("vectors must be two-dimensional.")

        if len(self.texts) != self.vectors.shape[0]:
            raise ValueError(
                "texts count must match the number of vectors."
            )

        if self.dimension <= 0:
            raise ValueError("dimension must be greater than zero.")

        if self.vectors.shape[1] != self.dimension:
            raise ValueError(
                "dimension must match the vector width."
            )
