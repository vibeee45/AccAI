from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FailureType(str, Enum):
    VALIDATION = "validation"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    PROCESSING = "processing"
    UNKNOWN = "unknown"


class FailureAction(str, Enum):
    RETRY = "retry"
    REVIEW = "review"
    REJECT = "reject"


@dataclass(frozen=True)
class FailureDetail:
    code: str
    message: str
    failure_type: FailureType
    action: FailureAction

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError(
                "code cannot be empty."
            )

        if not self.message.strip():
            raise ValueError(
                "message cannot be empty."
            )

        if not isinstance(
            self.failure_type,
            FailureType,
        ):
            raise TypeError(
                "failure_type must be FailureType."
            )

        if not isinstance(
            self.action,
            FailureAction,
        ):
            raise TypeError(
                "action must be FailureAction."
            )


@dataclass(frozen=True)
class FailureHandlingResult:
    success: bool
    requires_review: bool
    retryable: bool
    failure: FailureDetail | None = None
    errors: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.success,
            bool,
        ):
            raise TypeError(
                "success must be bool."
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
            self.errors,
            tuple,
        ):
            raise TypeError(
                "errors must be a tuple."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )

        if self.success and self.failure is not None:
            raise ValueError(
                "Successful result cannot contain a failure."
            )

        if not self.success and self.failure is None:
            raise ValueError(
                "Failed result must contain a failure."
            )

        if self.success and self.requires_review:
            raise ValueError(
                "Successful result cannot require review."
            )

        if self.success and self.retryable:
            raise ValueError(
                "Successful result cannot be retryable."
            )
