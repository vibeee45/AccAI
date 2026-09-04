from __future__ import annotations

from ..confidence.schemas import ConfidenceScore
from .config import LowConfidenceConfig
from .detector import LowConfidenceDetector
from .schemas import LowConfidenceDetection


class LowConfidenceService:
    """
    Service layer for low-confidence detection.
    """

    def __init__(
        self,
        detector: LowConfidenceDetector | None = None,
        config: LowConfidenceConfig | None = None,
    ) -> None:
        if detector is not None and config is not None:
            raise ValueError(
                "Provide either detector or config, not both."
            )

        self.detector = detector or LowConfidenceDetector(config)

    def detect(
        self,
        score: ConfidenceScore,
    ) -> LowConfidenceDetection:
        return self.detector.detect(score)

    def is_ready(self) -> bool:
        return self.detector.is_ready()
