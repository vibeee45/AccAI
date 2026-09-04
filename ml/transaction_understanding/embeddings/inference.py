from __future__ import annotations

from .config import EmbeddingConfig
from .embedder import TransactionEmbedder
from .schemas import BatchEmbeddingResult, EmbeddingResult


class EmbeddingService:
    def __init__(
        self,
        config: EmbeddingConfig | None = None,
    ) -> None:
        self.embedder = TransactionEmbedder(config)

    def embed(self, text: str) -> EmbeddingResult:
        return self.embedder.embed(text)

    def embed_many(
        self,
        texts: list[str],
    ) -> BatchEmbeddingResult:
        return self.embedder.embed_many(texts)

    @property
    def dimension(self) -> int:
        return self.embedder.dimension

    def is_ready(self) -> bool:
        return self.embedder is not None
