from __future__ import annotations

from typing import Any

from .config import ConfidenceRoutingConfig
from .router import ConfidenceRouter
from .schemas import RoutingResult


class ConfidenceRoutingService:
    """
    Public service interface for confidence routing.
    """

    def __init__(
        self,
        config: ConfidenceRoutingConfig | None = None,
    ) -> None:
        self.router = ConfidenceRouter(
            config
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
        return self.router.route(
            confidence,
            requires_review=requires_review,
            failed=failed,
            retryable=retryable,
            metadata=metadata,
        )

    def route_many(
        self,
        confidences: list[float]
        | tuple[float, ...],
    ) -> tuple[RoutingResult, ...]:
        return self.router.route_many(
            confidences
        )

    def is_ready(self) -> bool:
        return True
