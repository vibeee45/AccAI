from collections.abc import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class AccountTextFeatures:
    """
    TF-IDF representation used for account similarity.
    """

    def __init__(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        min_df: int = 1,
        max_features: int | None = 50000,
    ) -> None:
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=ngram_range,
            min_df=min_df,
            max_features=max_features,
            sublinear_tf=True,
        )

        self._fitted = False

    @property
    def fitted(self) -> bool:
        return self._fitted

    def fit(
        self,
        texts: Iterable[str],
    ) -> "AccountTextFeatures":
        texts = tuple(texts)

        if not texts:
            raise ValueError(
                "Cannot fit features on empty text collection."
            )

        self.vectorizer.fit(texts)
        self._fitted = True

        return self

    def transform(self, texts: Iterable[str]):
        if not self._fitted:
            raise RuntimeError(
                "Feature extractor must be fitted before transform."
            )

        texts = tuple(texts)

        if not texts:
            raise ValueError(
                "Cannot transform empty text collection."
            )

        return self.vectorizer.transform(texts)

    def similarity(
        self,
        query: str,
        candidates: Iterable[str],
    ) -> list[float]:
        candidate_texts = tuple(candidates)

        if not candidate_texts:
            raise ValueError(
                "Candidate texts cannot be empty."
            )

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not self._fitted:
            self.fit(
                candidate_texts
            )

        query_matrix = self.transform([query])
        candidate_matrix = self.transform(
            candidate_texts
        )

        similarities = cosine_similarity(
            query_matrix,
            candidate_matrix,
        )[0]

        return [
            float(value)
            for value in similarities
        ]

    def vocabulary_size(self) -> int:
        if not self._fitted:
            return 0

        return len(
            self.vectorizer.vocabulary_
        )
