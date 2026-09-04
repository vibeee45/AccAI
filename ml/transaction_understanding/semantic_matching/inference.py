from __future__ import annotations

from ml.transaction_understanding.embeddings.embedder import (
    TransactionEmbedder,
)

from .config import SemanticMatchingConfig
from .matcher import SemanticMatcher
from .schemas import SemanticMatchResult


class SemanticMatchingService:
    def __init__(
        self,
        embedder: TransactionEmbedder,
        config: SemanticMatchingConfig | None = None,
    ) -> None:
        self.matcher = SemanticMatcher(
            embedder=embedder,
            config=config,
        )

    def match(
        self,
        query: str,
        candidates: list[str],
    ) -> SemanticMatchResult:
        return self.matcher.match(
            query=query,
            candidates=candidates,
        )

    def is_ready(self) -> bool:
        return self.matcher is not None
