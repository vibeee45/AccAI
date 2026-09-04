import numpy as np
import pytest

from ml.transaction_understanding.embeddings.config import EmbeddingConfig
from ml.transaction_understanding.embeddings.embedder import TransactionEmbedder
from ml.transaction_understanding.embeddings.inference import EmbeddingService
from ml.transaction_understanding.embeddings.model import SentenceTransformerModel
from ml.transaction_understanding.embeddings.schemas import (
    BatchEmbeddingResult,
    EmbeddingResult,
)


class FakeEmbeddingModel:
    def __init__(self, dimension: int = 8):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(
        self,
        texts: list[str],
        *,
        normalize_embeddings: bool,
        batch_size: int,
    ) -> np.ndarray:
        vectors = []

        for text in texts:
            value = float(len(text))

            vector = np.full(
                self._dimension,
                value,
                dtype=np.float32,
            )

            if normalize_embeddings:
                norm = np.linalg.norm(vector)

                if norm > 0:
                    vector = vector / norm

            vectors.append(vector)

        return np.asarray(vectors, dtype=np.float32)


def test_default_config():
    config = EmbeddingConfig()

    assert config.model_name == "all-MiniLM-L6-v2"
    assert config.normalize_embeddings is True
    assert config.batch_size == 32
    assert config.max_length == 256


def test_config_custom_values():
    config = EmbeddingConfig(
        model_name="custom-model",
        normalize_embeddings=False,
        batch_size=64,
        max_length=128,
    )

    assert config.model_name == "custom-model"
    assert config.normalize_embeddings is False
    assert config.batch_size == 64
    assert config.max_length == 128


def test_config_rejects_empty_model_name():
    with pytest.raises(ValueError):
        EmbeddingConfig(model_name="")


def test_config_rejects_invalid_batch_size():
    with pytest.raises(ValueError):
        EmbeddingConfig(batch_size=0)


def test_config_rejects_invalid_max_length():
    with pytest.raises(ValueError):
        EmbeddingConfig(max_length=0)


def test_config_rejects_non_boolean_normalization():
    with pytest.raises(TypeError):
        EmbeddingConfig(normalize_embeddings="yes")


def test_embedding_result():
    vector = np.ones(8, dtype=np.float32)

    result = EmbeddingResult(
        text="cash sales rs 1000",
        vector=vector,
        dimension=8,
    )

    assert result.text == "cash sales rs 1000"
    assert result.dimension == 8
    assert result.vector.shape == (8,)


def test_embedding_result_rejects_empty_text():
    with pytest.raises(ValueError):
        EmbeddingResult(
            text="",
            vector=np.ones(8),
            dimension=8,
        )


def test_embedding_result_rejects_wrong_vector_type():
    with pytest.raises(TypeError):
        EmbeddingResult(
            text="cash sales",
            vector=[1, 2, 3],
            dimension=3,
        )


def test_embedding_result_rejects_two_dimensional_vector():
    with pytest.raises(ValueError):
        EmbeddingResult(
            text="cash sales",
            vector=np.ones((2, 4)),
            dimension=8,
        )


def test_embedding_result_rejects_dimension_mismatch():
    with pytest.raises(ValueError):
        EmbeddingResult(
            text="cash sales",
            vector=np.ones(8),
            dimension=4,
        )


def test_batch_embedding_result():
    vectors = np.ones((2, 8), dtype=np.float32)

    result = BatchEmbeddingResult(
        texts=["cash sales", "rent paid"],
        vectors=vectors,
        dimension=8,
    )

    assert len(result.texts) == 2
    assert result.vectors.shape == (2, 8)
    assert result.dimension == 8


def test_batch_embedding_result_rejects_empty_texts():
    with pytest.raises(ValueError):
        BatchEmbeddingResult(
            texts=[],
            vectors=np.ones((0, 8)),
            dimension=8,
        )


def test_batch_embedding_result_rejects_wrong_vector_type():
    with pytest.raises(TypeError):
        BatchEmbeddingResult(
            texts=["cash sales"],
            vectors=[[1, 2, 3]],
            dimension=3,
        )


def test_batch_embedding_result_rejects_one_dimensional_vectors():
    with pytest.raises(ValueError):
        BatchEmbeddingResult(
            texts=["cash sales"],
            vectors=np.ones(8),
            dimension=8,
        )


def test_batch_embedding_result_rejects_count_mismatch():
    with pytest.raises(ValueError):
        BatchEmbeddingResult(
            texts=["cash sales", "rent"],
            vectors=np.ones((1, 8)),
            dimension=8,
        )


def test_batch_embedding_result_rejects_dimension_mismatch():
    with pytest.raises(ValueError):
        BatchEmbeddingResult(
            texts=["cash sales"],
            vectors=np.ones((1, 8)),
            dimension=4,
        )


def test_embed_single_transaction():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel(8)
    )

    result = embedder.embed(
        "Received cash from customer rs 5000"
    )

    assert isinstance(result, EmbeddingResult)
    assert result.text == "Received cash from customer rs 5000"
    assert result.dimension == 8
    assert result.vector.shape == (8,)


def test_embed_many_transactions():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel(8)
    )

    result = embedder.embed_many(
        [
            "Cash sales rs 1000",
            "Paid rent rs 5000",
            "Purchased furniture rs 20000",
        ]
    )

    assert isinstance(result, BatchEmbeddingResult)
    assert len(result.texts) == 3
    assert result.vectors.shape == (3, 8)


def test_embedding_vectors_are_normalized():
    embedder = TransactionEmbedder(
        config=EmbeddingConfig(normalize_embeddings=True),
        model=FakeEmbeddingModel(8),
    )

    result = embedder.embed(
        "Cash sales rs 1000"
    )

    norm = np.linalg.norm(result.vector)

    assert np.isclose(norm, 1.0)


def test_embedding_vectors_can_be_unnormalized():
    embedder = TransactionEmbedder(
        config=EmbeddingConfig(normalize_embeddings=False),
        model=FakeEmbeddingModel(8),
    )

    result = embedder.embed(
        "Cash sales rs 1000"
    )

    norm = np.linalg.norm(result.vector)

    assert norm > 1.0


def test_dimension_property():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel(16)
    )

    assert embedder.dimension == 16


def test_embed_rejects_non_string():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel()
    )

    with pytest.raises(TypeError):
        embedder.embed(123)


def test_embed_rejects_empty_text():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel()
    )

    with pytest.raises(ValueError):
        embedder.embed("")


def test_embed_many_rejects_empty_list():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel()
    )

    with pytest.raises(ValueError):
        embedder.embed_many([])


def test_embed_many_rejects_invalid_text():
    embedder = TransactionEmbedder(
        model=FakeEmbeddingModel()
    )

    with pytest.raises(ValueError):
        embedder.embed_many(
            ["cash sales", "", "rent paid"]
        )


def test_service_embed():
    service = EmbeddingService.__new__(EmbeddingService)

    service.embedder = TransactionEmbedder(
        model=FakeEmbeddingModel(8)
    )

    result = service.embed("cash sales rs 1000")

    assert isinstance(result, EmbeddingResult)
    assert result.dimension == 8


def test_service_embed_many():
    service = EmbeddingService.__new__(EmbeddingService)

    service.embedder = TransactionEmbedder(
        model=FakeEmbeddingModel(8)
    )

    result = service.embed_many(
        ["cash sales", "rent paid"]
    )

    assert isinstance(result, BatchEmbeddingResult)
    assert result.vectors.shape == (2, 8)


def test_service_dimension():
    service = EmbeddingService.__new__(EmbeddingService)

    service.embedder = TransactionEmbedder(
        model=FakeEmbeddingModel(12)
    )

    assert service.dimension == 12


def test_service_is_ready():
    service = EmbeddingService.__new__(EmbeddingService)

    service.embedder = TransactionEmbedder(
        model=FakeEmbeddingModel()
    )

    assert service.is_ready() is True


def test_real_model_wrapper_has_expected_interface():
    assert hasattr(SentenceTransformerModel, "encode")
    assert hasattr(SentenceTransformerModel, "dimension")
