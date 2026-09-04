from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..confidence.schemas import ConfidenceScore


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    REVIEW_REQUIRED = "review_required"
    LOW = "low"


@dataclass(frozen=True)
class LowConfidenceSignal:
    """
    Identifies one confidence component that may require attention.
    """

    name: str
    value: float
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name cannot be empty.")

        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                "value must be between 0 and 1."
            )

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason cannot be empty.")


@dataclass(frozen=True)
class LowConfidenceDetection:
    """
    Result of confidence diagnosis.

    This object does not perform routing. Routing remains the
    responsibility of the existing confidence router.
    """

    overall: float
    level: ConfidenceLevel
    requires_review: bool
    signals: tuple[LowConfidenceSignal, ...]
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall <= 1.0:
            raise ValueError(
                "overall must be between 0 and 1."
            )

        if not isinstance(self.level, ConfidenceLevel):
            raise TypeError(
                "level must be ConfidenceLevel."
            )

        if not isinstance(self.requires_review, bool):
            raise TypeError(
                "requires_review must be a boolean."
            )

        if not isinstance(self.signals, tuple):
            raise TypeError(
                "signals must be a tuple."
            )

        if any(
            not isinstance(signal, LowConfidenceSignal)
            for signal in self.signals
        ):
            raise TypeError(
                "All signals must be LowConfidenceSignal."
            )

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason cannot be empty.")
