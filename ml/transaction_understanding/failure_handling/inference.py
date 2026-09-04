from __future__ import annotations

from typing import Any

from .config import FailureHandlingConfig
from .handler import FailureHandler
from .schemas import FailureHandlingResult


class FailureHandlingService:
    """
    Public service interface for failure handling.
    """

    def __init__(
        self,
        config: FailureHandlingConfig | None = None,
    ) -> None:
        self.handler = FailureHandler(
            config
        )

    def handle_exception(
        self,
        exception: Exception,
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        return self.handler.handle_exception(
            exception,
            metadata=metadata,
        )

    def handle_validation_failure(
        self,
        errors: list[str]
        | tuple[str, ...],
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        return self.handler.handle_validation_failure(
            errors,
            metadata=metadata,
        )

    def handle_success(
        self,
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        return self.handler.handle_success(
            metadata=metadata
        )

    def handle(
        self,
        operation: Any,
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        return self.handler.handle(
            operation,
            metadata=metadata,
        )

    def is_ready(self) -> bool:
        return True
