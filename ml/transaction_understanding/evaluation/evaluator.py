from __future__ import annotations

from typing import Sequence

from .config import EvaluationConfig
from .metrics import (
    classification_metrics,
    confidence_metrics,
    per_class_metrics,
)
from .schemas import (
    ClassMetrics,
    ClassificationMetrics,
    ConfidenceMetrics,
    EvaluationReport,
)


class ModelEvaluator:
    def __init__(
        self,
        config: EvaluationConfig | None = None,
    ) -> None:
        self.config = config or EvaluationConfig()

    def evaluate_classification(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        task: str = "classification",
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        metrics = classification_metrics(
            y_true,
            y_pred,
            zero_division=self.config.zero_division,
        )

        classification = ClassificationMetrics(
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1=metrics["f1"],
            support=metrics["support"],
        )

        raw_class_metrics = per_class_metrics(
            y_true,
            y_pred,
            zero_division=self.config.zero_division,
        )

        class_metrics = [
            ClassMetrics(
                label=label,
                precision=values["precision"],
                recall=values["recall"],
                f1=values["f1"],
                support=values["support"],
            )
            for label, values
            in raw_class_metrics.items()
        ]

        confidence_result = None

        if confidences is not None:
            raw_confidence = confidence_metrics(
                y_true,
                y_pred,
                confidences,
                bins=self.config.confidence_bins,
            )

            confidence_result = ConfidenceMetrics(
                mean_confidence=raw_confidence[
                    "mean_confidence"
                ],
                accuracy=raw_confidence[
                    "accuracy"
                ],
                calibration_error=raw_confidence[
                    "calibration_error"
                ],
            )

        return EvaluationReport(
            task=task,
            metrics=classification,
            class_metrics=class_metrics,
            confidence_metrics=confidence_result,
        )

    def evaluate_account_identification(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluate_classification(
            y_true,
            y_pred,
            task="account_identification",
            confidences=confidences,
        )

    def evaluate_debit_credit(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluate_classification(
            y_true,
            y_pred,
            task="debit_credit",
            confidences=confidences,
        )

    def evaluate_payment_mode(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluate_classification(
            y_true,
            y_pred,
            task="payment_mode",
            confidences=confidences,
        )

    def is_ready(self) -> bool:
        return True
