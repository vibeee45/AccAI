from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    support: int

    def __post_init__(self) -> None:
        for name, value in (
            ("accuracy", self.accuracy),
            ("precision", self.precision),
            ("recall", self.recall),
            ("f1", self.f1),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1."
                )

        if self.support < 0:
            raise ValueError(
                "support cannot be negative."
            )


@dataclass(frozen=True)
class ClassMetrics:
    label: str
    precision: float
    recall: float
    f1: float
    support: int

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError(
                "label cannot be empty."
            )

        for name, value in (
            ("precision", self.precision),
            ("recall", self.recall),
            ("f1", self.f1),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1."
                )

        if self.support < 0:
            raise ValueError(
                "support cannot be negative."
            )


@dataclass(frozen=True)
class ConfidenceMetrics:
    mean_confidence: float
    accuracy: float
    calibration_error: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.mean_confidence <= 1.0:
            raise ValueError(
                "mean_confidence must be between 0 and 1."
            )

        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError(
                "accuracy must be between 0 and 1."
            )

        if self.calibration_error < 0.0:
            raise ValueError(
                "calibration_error cannot be negative."
            )


@dataclass(frozen=True)
class EvaluationReport:
    task: str
    metrics: ClassificationMetrics
    class_metrics: list[ClassMetrics] = field(
        default_factory=list
    )
    confidence_metrics: ConfidenceMetrics | None = None

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError(
                "task cannot be empty."
            )

        if not isinstance(
            self.metrics,
            ClassificationMetrics,
        ):
            raise TypeError(
                "metrics must be ClassificationMetrics."
            )
