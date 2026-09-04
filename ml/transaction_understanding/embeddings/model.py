from __future__ import annotations

from typing import Protocol

import numpy as np


class EmbeddingModel(Protocol):
    @property
    def dimension(self) -> int:
        ...

    def encode(
        self,
        texts: list[str],
        *,
        normalize_embeddings: bool,
        batch_size: int,
    ) -> np.ndarray:
        ...


class SentenceTransformerModel:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        self._model = SentenceTransformer(model_name)

    @property
    def dimension(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def encode(
        self,
        texts: list[str],
        *,
        normalize_embeddings: bool,
        batch_size: int,
    ) -> np.ndarray:
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return np.asarray(vectors, dtype=np.float32)
