from __future__ import annotations

import numpy as np

from .config import EmbeddingConfig
from .model import EmbeddingModel, SentenceTransformerModel
from .schemas import BatchEmbeddingResult, EmbeddingResult


class TransactionEmbedder:
    def __init__(
        self,
        config: EmbeddingConfig | None = None,
        model: EmbeddingModel | None = None,
    ) -> None:
        self.config = config or EmbeddingConfig()

        self.model = model or SentenceTransformerModel(
            self.config.model_name
        )

    def embed(self, text: str) -> EmbeddingResult:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")

        if not text.strip():
            raise ValueError("text cannot be empty.")

        result = self.embed_many([text])

        return EmbeddingResult(
            text=text,
            vector=result.vectors[0],
            dimension=result.dimension,
        )

    def embed_many(
        self,
        texts: list[str],
    ) -> BatchEmbeddingResult:
        if not texts:
            raise ValueError("texts cannot be empty.")

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "texts must contain only non-empty strings."
            )

        vectors = self.model.encode(
            texts,
            normalize_embeddings=self.config.normalize_embeddings,
            batch_size=self.config.batch_size,
        )

        if vectors.ndim != 2:
            raise ValueError(
                "Embedding model must return a two-dimensional array."
            )

        return BatchEmbeddingResult(
            texts=list(texts),
            vectors=vectors,
            dimension=self.model.dimension,
        )

    @property
    def dimension(self) -> int:
        return self.model.dimension
