from collections.abc import Iterable

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import ClassificationConfig


class TransactionTextFeatures:
    """
    TF-IDF feature representation for transaction narration.
    """

    def __init__(
        self,
        config: ClassificationConfig | None = None,
    ) -> None:
        self.config = config or ClassificationConfig()

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            min_df=self.config.min_df,
            max_features=self.config.max_features,
            ngram_range=(
                self.config.ngram_min,
                self.config.ngram_max,
            ),
            sublinear_tf=True,
        )

        self._fitted = False

    @property
    def fitted(self) -> bool:
        return self._fitted

    def fit(
        self,
        texts: Iterable[str],
    ) -> "TransactionTextFeatures":
        texts = tuple(texts)

        if not texts:
            raise ValueError(
                "Cannot fit feature extractor on empty text."
            )

        self.vectorizer.fit(texts)
        self._fitted = True

        return self

    def transform(
        self,
        texts: Iterable[str],
    ) -> csr_matrix:
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

    def fit_transform(
        self,
        texts: Iterable[str],
    ) -> csr_matrix:
        texts = tuple(texts)

        if not texts:
            raise ValueError(
                "Cannot fit on empty text collection."
            )

        matrix = self.vectorizer.fit_transform(texts)
        self._fitted = True

        return matrix

    def vocabulary_size(self) -> int:
        if not self._fitted:
            return 0

        return len(
            self.vectorizer.vocabulary_
        )
