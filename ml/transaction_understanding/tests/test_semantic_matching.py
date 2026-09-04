import numpy as np
import pytest

from ml.transaction_understanding.embeddings.embedder import (
    TransactionEmbedder,
)
from ml.transaction_understanding.semantic_matching.config import (
    SemanticMatchingConfig,
)
from ml.transaction_understanding.semantic_matching.inference import (
    SemanticMatchingService,
)
from ml.transaction_understanding.semantic_matching.matcher import (
    SemanticMatcher,
)
from ml.transaction_understanding.semantic_matching.schemas import (
    SemanticMatch,
    SemanticMatchResult,
)


class FakeEmbedder:
    def embed(self, text: str):
        from ml.transaction_understanding.embeddings.schemas import (
            EmbeddingResult,
        )

        vectors = {
            "cash sales": np.array(
                [1.0, 0.0, 0.0],
                dtype=np.float32,
            ),
            "cash received from customer": np.array(
                [0.99, 0.1, 0.0],
                dtype=np.float32,
            ),
            "paid office rent": np.array(
                [0.0, 1.0, 0.0],
                dtype=np.float32,
            ),
            "purchased laptop": np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32,
            ),
            "completely unrelated": np.array(
                [-1.0, 0.0, 0.0],
                dtype=np.float32,
            ),
        }

        vector = vectors.get(
            text,
            np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32,
            ),
        )

        return EmbeddingResult(
            text=text,
            vector=vector,
            dimension=3,
        )

    def embed_many(self, texts: list[str]):
        from ml.transaction_understanding.embeddings.schemas import (
            BatchEmbeddingResult,
        )

        vectors = np.asarray(
            [
                self.embed(text).vector
                for text in texts
            ],
            dtype=np.float32,
        )

        return BatchEmbeddingResult(
            texts=list(texts),
            vectors=vectors,
            dimension=3,
        )


def test_default_config():
    config = SemanticMatchingConfig()

    assert config.similarity_threshold == 0.70
    assert config.top_k == 5


def test_custom_config():
    config = SemanticMatchingConfig(
        similarity_threshold=0.85,
        top_k=3,
    )

    assert config.similarity_threshold == 0.85
    assert config.top_k == 3


def test_invalid_similarity_threshold():
    with pytest.raises(ValueError):
        SemanticMatchingConfig(
            similarity_threshold=1.5
        )


def test_negative_similarity_threshold():
    with pytest.raises(ValueError):
        SemanticMatchingConfig(
            similarity_threshold=-0.1
        )


def test_invalid_top_k():
    with pytest.raises(ValueError):
        SemanticMatchingConfig(top_k=0)


def test_semantic_match_schema():
    result = SemanticMatch(
        index=0,
        text="cash sales",
        similarity=0.95,
    )

    assert result.index == 0
    assert result.text == "cash sales"
    assert result.similarity == 0.95


def test_semantic_match_rejects_negative_index():
    with pytest.raises(ValueError):
        SemanticMatch(
            index=-1,
            text="cash sales",
            similarity=0.95,
        )


def test_semantic_match_rejects_empty_text():
    with pytest.raises(ValueError):
        SemanticMatch(
            index=0,
            text="",
            similarity=0.95,
        )


def test_semantic_match_rejects_invalid_similarity():
    with pytest.raises(ValueError):
        SemanticMatch(
            index=0,
            text="cash sales",
            similarity=1.5,
        )


def test_result_schema():
    match = SemanticMatch(
        index=0,
        text="cash sales",
        similarity=0.95,
    )

    result = SemanticMatchResult(
        query="cash sales",
        matches=[match],
    )

    assert result.query == "cash sales"
    assert len(result.matches) == 1


def test_result_rejects_empty_query():
    with pytest.raises(ValueError):
        SemanticMatchResult(
            query="",
            matches=[],
        )


def test_result_rejects_non_list_matches():
    with pytest.raises(TypeError):
        SemanticMatchResult(
            query="cash sales",
            matches=(),
        )


def test_cosine_similarity_identical_vectors():
    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    candidates = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    scores = SemanticMatcher.cosine_similarity(
        query,
        candidates,
    )

    assert np.isclose(scores[0], 1.0)
    assert np.isclose(scores[1], 0.0)


def test_cosine_similarity_opposite_vectors():
    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    candidates = np.array(
        [[-1.0, 0.0, 0.0]],
        dtype=np.float32,
    )

    scores = SemanticMatcher.cosine_similarity(
        query,
        candidates,
    )

    assert np.isclose(scores[0], -1.0)


def test_cosine_similarity_rejects_zero_query():
    query = np.zeros(3)

    candidates = np.ones((2, 3))

    with pytest.raises(ValueError):
        SemanticMatcher.cosine_similarity(
            query,
            candidates,
        )


def test_cosine_similarity_rejects_zero_candidate():
    query = np.ones(3)

    candidates = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )

    with pytest.raises(ValueError):
        SemanticMatcher.cosine_similarity(
            query,
            candidates,
        )


def test_match_returns_similar_transactions():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    result = matcher.match(
        "cash sales",
        [
            "cash received from customer",
            "paid office rent",
            "purchased laptop",
        ],
    )

    assert result.query == "cash sales"
    assert len(result.matches) >= 1
    assert result.matches[0].text == (
        "cash received from customer"
    )


def test_match_ranks_by_similarity():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    result = matcher.match(
        "cash sales",
        [
            "purchased laptop",
            "cash received from customer",
            "paid office rent",
        ],
    )

    assert result.matches[0].text == (
        "cash received from customer"
    )


def test_match_applies_threshold():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
        config=SemanticMatchingConfig(
            similarity_threshold=0.99,
        ),
    )

    result = matcher.match(
        "cash sales",
        [
            "cash received from customer",
            "paid office rent",
        ],
    )

    assert all(
        match.similarity >= 0.99
        for match in result.matches
    )


def test_match_applies_top_k():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
        config=SemanticMatchingConfig(
            similarity_threshold=0.0,
            top_k=1,
        ),
    )

    result = matcher.match(
        "cash sales",
        [
            "cash received from customer",
            "paid office rent",
            "purchased laptop",
        ],
    )

    assert len(result.matches) == 1


def test_match_can_return_no_matches():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
        config=SemanticMatchingConfig(
            similarity_threshold=0.99999,
        ),
    )

    result = matcher.match(
        "cash sales",
        [
            "paid office rent",
            "purchased laptop",
        ],
    )

    assert result.matches == []


def test_match_rejects_non_string_query():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    with pytest.raises(TypeError):
        matcher.match(
            123,
            ["cash sales"],
        )


def test_match_rejects_empty_query():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    with pytest.raises(ValueError):
        matcher.match(
            "",
            ["cash sales"],
        )


def test_match_rejects_empty_candidates():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    with pytest.raises(ValueError):
        matcher.match(
            "cash sales",
            [],
        )


def test_match_rejects_invalid_candidate():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    with pytest.raises(ValueError):
        matcher.match(
            "cash sales",
            ["cash sales", ""],
        )


def test_service_match():
    service = SemanticMatchingService(
        embedder=FakeEmbedder(),
    )

    result = service.match(
        "cash sales",
        ["cash received from customer"],
    )

    assert isinstance(
        result,
        SemanticMatchResult,
    )


def test_service_ready():
    service = SemanticMatchingService(
        embedder=FakeEmbedder(),
    )

    assert service.is_ready() is True


def test_similarity_values_are_bounded_for_normalized_vectors():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    result = matcher.match(
        "cash sales",
        [
            "cash received from customer",
            "paid office rent",
        ],
    )

    for match in result.matches:
        assert 0.0 <= match.similarity <= 1.0


def test_original_candidate_indices_are_preserved():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
        config=SemanticMatchingConfig(
            similarity_threshold=0.0,
            top_k=5,
        ),
    )

    candidates = [
        "purchased laptop",
        "cash received from customer",
        "paid office rent",
    ]

    result = matcher.match(
        "cash sales",
        candidates,
    )

    for match in result.matches:
        assert candidates[match.index] == match.text


def test_match_preserves_query():
    matcher = SemanticMatcher(
        embedder=FakeEmbedder(),
    )

    query = "cash sales"

    result = matcher.match(
        query,
        ["cash received from customer"],
    )

    assert result.query == query
