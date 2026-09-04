from __future__ import annotations

from typing import Sequence

from .config import EvaluationConfig
from .evaluator import ModelEvaluator
from .schemas import EvaluationReport


class EvaluationService:
    def __init__(
        self,
        config: EvaluationConfig | None = None,
    ) -> None:
        self.evaluator = ModelEvaluator(config)

    def evaluate_classification(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        task: str = "classification",
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluator.evaluate_classification(
            y_true,
            y_pred,
            task=task,
            confidences=confidences,
        )

    def evaluate_account_identification(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluator.evaluate_account_identification(
            y_true,
            y_pred,
            confidences=confidences,
        )

    def evaluate_debit_credit(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluator.evaluate_debit_credit(
            y_true,
            y_pred,
            confidences=confidences,
        )

    def evaluate_payment_mode(
        self,
        y_true: Sequence[str],
        y_pred: Sequence[str],
        *,
        confidences: Sequence[float] | None = None,
    ) -> EvaluationReport:
        return self.evaluator.evaluate_payment_mode(
            y_true,
            y_pred,
            confidences=confidences,
        )

    def is_ready(self) -> bool:
        return self.evaluator.is_ready()
