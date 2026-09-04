from __future__ import annotations

from typing import Any

from .config import ConfidenceRoutingConfig
from .schemas import (
    RoutingDecision,
    RoutingResult,
)


class ConfidenceRouter:
    """
    Routes transactions according to AI confidence.

    High confidence:
        Automatic processing.

    Medium confidence:
        Human review.

    Low confidence:
        Rejection / manual intervention.

    This layer does not modify accounting data.
    """

    def __init__(
        self,
        config: ConfidenceRoutingConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else ConfidenceRoutingConfig()
        )

    def route(
        self,
        confidence: float,
        *,
        requires_review: bool = False,
        failed: bool = False,
        retryable: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> RoutingResult:
        if not isinstance(
            confidence,
            (int, float),
        ) or isinstance(
            confidence,
            bool,
        ):
            raise TypeError(
                "confidence must be numeric."
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(
            requires_review,
            bool,
        ):
            raise TypeError(
                "requires_review must be bool."
            )

        if not isinstance(
            failed,
            bool,
        ):
            raise TypeError(
                "failed must be bool."
            )

        if not isinstance(
            retryable,
            bool,
        ):
            raise TypeError(
                "retryable must be bool."
            )

        base_metadata = (
            dict(metadata)
            if metadata is not None
            else {}
        )

        if failed:
            return RoutingResult(
                decision=RoutingDecision.REJECT,
                confidence=float(confidence),
                reason=(
                    "Transaction processing failed "
                    "and cannot proceed automatically."
                ),
                requires_review=True,
                retryable=retryable,
                metadata=base_metadata,
            )

        if requires_review:
            return RoutingResult(
                decision=RoutingDecision.HUMAN_REVIEW,
                confidence=float(confidence),
                reason=(
                    "Transaction was explicitly marked "
                    "for human review."
                ),
                requires_review=True,
                retryable=False,
                metadata=base_metadata,
            )

        if (
            confidence
            >= self.config.auto_process_threshold
        ):
            return RoutingResult(
                decision=RoutingDecision.AUTO_PROCESS,
                confidence=float(confidence),
                reason=(
                    "Confidence meets the automatic "
                    "processing threshold."
                ),
                requires_review=False,
                retryable=False,
                metadata=base_metadata,
            )

        if (
            confidence
            >= self.config.review_threshold
        ):
            return RoutingResult(
                decision=RoutingDecision.HUMAN_REVIEW,
                confidence=float(confidence),
                reason=(
                    "Confidence is below the automatic "
                    "processing threshold and requires "
                    "human review."
                ),
                requires_review=True,
                retryable=False,
                metadata=base_metadata,
            )

        return RoutingResult(
            decision=RoutingDecision.REJECT,
            confidence=float(confidence),
            reason=(
                "Confidence is too low for safe "
                "automatic accounting processing."
            ),
            requires_review=True,
            retryable=False,
            metadata=base_metadata,
        )

    def route_many(
        self,
        confidences: list[float]
        | tuple[float, ...],
    ) -> tuple[RoutingResult, ...]:
        return tuple(
            self.route(confidence)
            for confidence in confidences
        )
