from __future__ import annotations

from typing import Any

from .config import FailureHandlingConfig
from .schemas import (
    FailureAction,
    FailureDetail,
    FailureHandlingResult,
    FailureType,
)


class FailureHandler:
    """
    Converts exceptions and processing failures into
    structured, safe results.

    This layer never silently ignores a failure.
    """

    def __init__(
        self,
        config: FailureHandlingConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else FailureHandlingConfig()
        )

    def _truncate(
        self,
        message: str,
    ) -> str:
        if not self.config.capture_exception_details:
            return "Processing failed."

        return message[
            : self.config.max_error_message_length
        ]

    @staticmethod
    def _classify_exception(
        exception: Exception,
    ) -> tuple[
        FailureType,
        FailureAction,
        str,
    ]:
        if isinstance(exception, TypeError):
            return (
                FailureType.TYPE_ERROR,
                FailureAction.REJECT,
                "TYPE_ERROR",
            )

        if isinstance(exception, ValueError):
            return (
                FailureType.VALUE_ERROR,
                FailureAction.REVIEW,
                "VALUE_ERROR",
            )

        return (
            FailureType.PROCESSING,
            FailureAction.RETRY,
            "PROCESSING_ERROR",
        )

    def handle_exception(
        self,
        exception: Exception,
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        if not isinstance(
            exception,
            Exception,
        ):
            raise TypeError(
                "exception must be an Exception."
            )

        (
            failure_type,
            action,
            code,
        ) = self._classify_exception(
            exception
        )

        failure = FailureDetail(
            code=code,
            message=self._truncate(
                str(exception)
            ),
            failure_type=failure_type,
            action=action,
        )

        return FailureHandlingResult(
            success=False,
            requires_review=(
                action == FailureAction.REVIEW
            ),
            retryable=(
                action == FailureAction.RETRY
            ),
            failure=failure,
            errors=(
                failure.message,
            ),
            metadata=(
                dict(metadata)
                if (
                    self.config.preserve_metadata
                    and metadata is not None
                )
                else {}
            ),
        )

    def handle_validation_failure(
        self,
        errors: list[str]
        | tuple[str, ...],
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        if not isinstance(
            errors,
            (list, tuple),
        ):
            raise TypeError(
                "errors must be list or tuple."
            )

        cleaned_errors = tuple(
            str(error).strip()
            for error in errors
            if str(error).strip()
        )

        if not cleaned_errors:
            raise ValueError(
                "At least one validation error is required."
            )

        message = "; ".join(
            cleaned_errors
        )

        failure = FailureDetail(
            code="VALIDATION_FAILED",
            message=self._truncate(
                message
            ),
            failure_type=FailureType.VALIDATION,
            action=FailureAction.REVIEW,
        )

        return FailureHandlingResult(
            success=False,
            requires_review=True,
            retryable=False,
            failure=failure,
            errors=cleaned_errors,
            metadata=(
                dict(metadata)
                if (
                    self.config.preserve_metadata
                    and metadata is not None
                )
                else {}
            ),
        )

    def handle_success(
        self,
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        return FailureHandlingResult(
            success=True,
            requires_review=False,
            retryable=False,
            failure=None,
            errors=(),
            metadata=(
                dict(metadata)
                if (
                    self.config.preserve_metadata
                    and metadata is not None
                )
                else {}
            ),
        )

    def handle(
        self,
        operation: Any,
        metadata: dict[str, Any] | None = None,
    ) -> FailureHandlingResult:
        if not callable(operation):
            raise TypeError(
                "operation must be callable."
            )

        try:
            operation()
        except Exception as exc:
            return self.handle_exception(
                exc,
                metadata=metadata,
            )

        return self.handle_success(
            metadata=metadata
        )
