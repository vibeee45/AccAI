from __future__ import annotations

from ..confidence.schemas import ConfidenceScore
from .config import LowConfidenceConfig
from .schemas import (
    ConfidenceLevel,
    LowConfidenceDetection,
    LowConfidenceSignal,
)


class LowConfidenceDetector:
    """
    Diagnoses confidence quality.

    Important architectural rule:

    - ConfidenceScorer calculates the confidence score.
    - LowConfidenceDetector diagnoses the score and weak signals.
    - ConfidenceRouter decides AUTO_PROCESS / HUMAN_REVIEW / REJECT.

    This keeps responsibilities separate.
    """

    def __init__(
        self,
        config: LowConfidenceConfig | None = None,
    ) -> None:
        self.config = config or LowConfidenceConfig()

    def detect(
        self,
        score: ConfidenceScore,
    ) -> LowConfidenceDetection:
        if not isinstance(score, ConfidenceScore):
            raise TypeError(
                "score must be ConfidenceScore."
            )

        overall = float(score.overall)

        level = self._classify_level(overall)

        signals = self._detect_weak_signals(score)

        requires_review = (
            level != ConfidenceLevel.HIGH
            or score.requires_review
        )

        reason = self._build_reason(
            score=score,
            level=level,
            signals=signals,
        )

        return LowConfidenceDetection(
            overall=overall,
            level=level,
            requires_review=requires_review,
            signals=tuple(signals),
            reason=reason,
        )

    def _classify_level(
        self,
        overall: float,
    ) -> ConfidenceLevel:
        if overall >= self.config.high_threshold:
            return ConfidenceLevel.HIGH

        if overall >= self.config.review_threshold:
            return ConfidenceLevel.REVIEW_REQUIRED

        return ConfidenceLevel.LOW

    def _detect_weak_signals(
        self,
        score: ConfidenceScore,
    ) -> list[LowConfidenceSignal]:
        signal_values = {
            "classification": score.signals.classification,
            "account": score.signals.account,
            "debit_credit": score.signals.debit_credit,
            "payment_mode": score.signals.payment_mode,
            "semantic": score.signals.semantic,
        }

        detected: list[LowConfidenceSignal] = []

        for name, value in signal_values.items():
            is_weak = (
                value <= self.config.weak_signal_threshold
                or (
                    value + self.config.signal_gap_threshold
                    < score.overall
                )
            )

            if not is_weak:
                continue

            detected.append(
                LowConfidenceSignal(
                    name=name,
                    value=float(value),
                    reason=self._signal_reason(
                        name=name,
                        value=value,
                    ),
                )
            )

        detected.sort(key=lambda item: item.value)

        return detected

    @staticmethod
    def _signal_reason(
        name: str,
        value: float,
    ) -> str:
        labels = {
            "classification": "transaction classification",
            "account": "account identification",
            "debit_credit": "debit/credit prediction",
            "payment_mode": "payment-mode detection",
            "semantic": "semantic matching",
        }

        label = labels.get(name, name)

        return (
            f"{label.capitalize()} confidence is "
            f"{value:.3f}, indicating a weak prediction signal."
        )

    def _build_reason(
        self,
        score: ConfidenceScore,
        level: ConfidenceLevel,
        signals: list[LowConfidenceSignal],
    ) -> str:
        if level == ConfidenceLevel.HIGH:
            if not signals:
                return (
                    f"Overall confidence is {score.overall:.3f}; "
                    "the prediction meets the high-confidence threshold."
                )

            names = ", ".join(
                signal.name
                for signal in signals
            )

            return (
                f"Overall confidence is {score.overall:.3f} and meets "
                "the high-confidence threshold, but weak signals were "
                f"detected in: {names}."
            )

        if level == ConfidenceLevel.REVIEW_REQUIRED:
            if signals:
                names = ", ".join(
                    signal.name
                    for signal in signals
                )

                return (
                    f"Overall confidence is {score.overall:.3f}; "
                    "human review is recommended. Weak signals: "
                    f"{names}."
                )

            return (
                f"Overall confidence is {score.overall:.3f}; "
                "human review is required because it is below the "
                "high-confidence threshold."
            )

        if signals:
            names = ", ".join(
                signal.name
                for signal in signals
            )

            return (
                f"Overall confidence is {score.overall:.3f}; "
                "the prediction is low-confidence and requires "
                f"attention. Weak signals: {names}."
            )

        return (
            f"Overall confidence is {score.overall:.3f}; "
            "the prediction is below the review threshold."
        )

    def is_ready(self) -> bool:
        return True
