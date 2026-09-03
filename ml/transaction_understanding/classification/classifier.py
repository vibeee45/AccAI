from collections.abc import Iterable

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

from .config import ClassificationConfig
from .dataset import ClassificationDataset
from .features import TransactionTextFeatures
from .schemas import (
    ClassificationMetrics,
    ClassificationPrediction,
)


class TransactionClassifier:
    """
    TF-IDF + Logistic Regression transaction classifier.

    The classifier predicts transaction semantics only.
    It does not perform accounting calculations.
    """

    def __init__(
        self,
        config: ClassificationConfig | None = None,
    ) -> None:
        self.config = config or ClassificationConfig()

        self.features = TransactionTextFeatures(
            self.config
        )

        self.model = LogisticRegression(
            C=self.config.classifier_c,
            max_iter=self.config.max_iter,
            random_state=self.config.random_state,
        )

        self._fitted = False

    @property
    def fitted(self) -> bool:
        return self._fitted

    @property
    def classes(self) -> tuple[str, ...]:
        if not self._fitted:
            return ()

        return tuple(
            str(value)
            for value in self.model.classes_
        )

    def fit(
        self,
        dataset: ClassificationDataset,
    ) -> "TransactionClassifier":
        dataset.validate_classes(
            self.config.classes
        )

        if len(dataset.classes) < 2:
            raise ValueError(
                "At least two transaction classes "
                "are required for classification."
            )

        x = self.features.fit_transform(
            dataset.texts
        )

        y = np.asarray(
            dataset.labels,
            dtype=str,
        )

        self.model.fit(x, y)
        self._fitted = True

        return self

    def predict(
        self,
        texts: Iterable[str],
    ) -> list[ClassificationPrediction]:
        if not self._fitted:
            raise RuntimeError(
                "Classifier must be fitted before prediction."
            )

        texts = tuple(texts)

        if not texts:
            raise ValueError(
                "Prediction input cannot be empty."
            )

        x = self.features.transform(texts)

        labels = self.model.predict(x)
        probabilities = self.model.predict_proba(x)

        results: list[ClassificationPrediction] = []

        for label, probability_row in zip(
            labels,
            probabilities,
        ):
            probability_map = {
                str(class_name): float(probability)
                for class_name, probability in zip(
                    self.model.classes_,
                    probability_row,
                )
            }

            confidence = float(
                np.max(probability_row)
            )

            results.append(
                ClassificationPrediction(
                    label=str(label),
                    confidence=confidence,
                    probabilities=probability_map,
                    requires_review=(
                        confidence
                        < self.config.confidence_threshold
                    ),
                )
            )

        return results

    def predict_one(
        self,
        text: str,
    ) -> ClassificationPrediction:
        return self.predict([text])[0]

    def evaluate(
        self,
        dataset: ClassificationDataset,
    ) -> ClassificationMetrics:
        if not self._fitted:
            raise RuntimeError(
                "Classifier must be fitted before evaluation."
            )

        predictions = self.predict(
            dataset.texts
        )

        y_true = dataset.labels
        y_pred = [
            prediction.label
            for prediction in predictions
        ]

        return ClassificationMetrics(
            accuracy=float(
                accuracy_score(
                    y_true,
                    y_pred,
                )
            ),
            precision_macro=float(
                precision_score(
                    y_true,
                    y_pred,
                    average="macro",
                    zero_division=0,
                )
            ),
            recall_macro=float(
                recall_score(
                    y_true,
                    y_pred,
                    average="macro",
                    zero_division=0,
                )
            ),
            f1_macro=float(
                f1_score(
                    y_true,
                    y_pred,
                    average="macro",
                    zero_division=0,
                )
            ),
            sample_count=len(dataset),
        )

    def vocabulary_size(self) -> int:
        return self.features.vocabulary_size()
