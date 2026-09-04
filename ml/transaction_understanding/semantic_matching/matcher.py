from __future__ import annotations

import numpy as np

from ml.transaction_understanding.embeddings.embedder import (
    TransactionEmbedder,
)

from .config import SemanticMatchingConfig
from .schemas import SemanticMatch, SemanticMatchResult


class SemanticMatcher:
    def __init__(
        self,
        embedder: TransactionEmbedder,
        config: SemanticMatchingConfig | None = None,
    ) -> None:
        self.embedder = embedder
        self.config = config or SemanticMatchingConfig()

    @staticmethod
    def cosine_similarity(
        query_vector: np.ndarray,
        candidate_vectors: np.ndarray,
    ) -> np.ndarray:
        query_norm = np.linalg.norm(query_vector)

        if query_norm == 0:
            raise ValueError(
                "query vector cannot have zero magnitude."
            )

        candidate_norms = np.linalg.norm(
            candidate_vectors,
            axis=1,
        )

        if np.any(candidate_norms == 0):
            raise ValueError(
                "candidate vectors cannot have zero magnitude."
            )

        return (
            candidate_vectors @ query_vector
        ) / (
            candidate_norms * query_norm
        )

    def match(
        self,
        query: str,
        candidates: list[str],
    ) -> SemanticMatchResult:
        if not isinstance(query, str):
            raise TypeError("query must be a string.")

        if not query.strip():
            raise ValueError("query cannot be empty.")

        if not candidates:
            raise ValueError(
                "candidates cannot be empty."
            )

        if any(
            not isinstance(candidate, str)
            or not candidate.strip()
            for candidate in candidates
        ):
            raise ValueError(
                "candidates must contain only "
                "non-empty strings."
            )

        query_result = self.embedder.embed(query)

        candidate_result = self.embedder.embed_many(
            candidates
        )

        similarities = self.cosine_similarity(
            query_result.vector,
            candidate_result.vectors,
        )

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        matches: list[SemanticMatch] = []

        for index in ranked_indices:
            similarity = float(similarities[index])

            if (
                similarity
                < self.config.similarity_threshold
            ):
                continue

            matches.append(
                SemanticMatch(
                    index=int(index),
                    text=candidates[index],
                    similarity=similarity,
                )
            )

            if len(matches) >= self.config.top_k:
                break

        return SemanticMatchResult(
            query=query,
            matches=matches,
        )
