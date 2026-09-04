from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RoutingDecision(str, Enum):
    AUTO_PROCESS = "auto_process"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"


@dataclass(frozen=True)
class RoutingResult:
    decision: RoutingDecision
    confidence: float
    reason: str
    requires_review: bool
    retryable: bool = False
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.decision,
            RoutingDecision,
        ):
            raise TypeError(
                "decision must be RoutingDecision."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )

        if not isinstance(
            self.requires_review,
            bool,
        ):
            raise TypeError(
                "requires_review must be bool."
            )

        if not isinstance(
            self.retryable,
            bool,
        ):
            raise TypeError(
                "retryable must be bool."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )

        if (
            self.decision
            == RoutingDecision.AUTO_PROCESS
        ):
            if self.requires_review:
                raise ValueError(
                    "AUTO_PROCESS cannot require review."
                )

            if self.retryable:
                raise ValueError(
                    "AUTO_PROCESS cannot be retryable."
                )

        if (
            self.decision
            == RoutingDecision.HUMAN_REVIEW
            and not self.requires_review
        ):
            raise ValueError(
                "HUMAN_REVIEW must require review."
            )
