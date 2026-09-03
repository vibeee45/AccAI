from .classifier import TransactionClassifier
from .config import ClassificationConfig
from .schemas import ClassificationPrediction


class TransactionClassificationService:
    """
    Application-facing service for transaction classification.

    Keeps model inference separate from API/business logic.
    """

    def __init__(
        self,
        classifier: TransactionClassifier | None = None,
    ) -> None:
        self.classifier = (
            classifier
            or TransactionClassifier(
                ClassificationConfig()
            )
        )

    @property
    def ready(self) -> bool:
        return self.classifier.fitted

    def classify(
        self,
        text: str,
    ) -> ClassificationPrediction:
        if not text or not text.strip():
            raise ValueError(
                "Transaction text cannot be empty."
            )

        return self.classifier.predict_one(
            text.strip()
        )

    def classify_many(
        self,
        texts: list[str],
    ) -> list[ClassificationPrediction]:
        if not texts:
            raise ValueError(
                "Transaction text collection cannot be empty."
            )

        return self.classifier.predict(texts)
