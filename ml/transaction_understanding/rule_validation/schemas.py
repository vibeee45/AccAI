from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


ZERO = Decimal("0")


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    REVIEW_REQUIRED = "review_required"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: ValidationSeverity

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
            self.severity,
            ValidationSeverity,
        ):
            raise TypeError(
                "severity must be ValidationSeverity."
            )


@dataclass(frozen=True)
class RuleValidationResult:
    status: ValidationStatus
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    confidence: float = 1.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ValidationStatus,
        ):
            raise TypeError(
                "status must be ValidationStatus."
            )

        if not isinstance(self.valid, bool):
            raise TypeError(
                "valid must be bool."
            )

        if not isinstance(self.issues, tuple):
            raise TypeError(
                "issues must be a tuple."
            )

        if not isinstance(self.warnings, tuple):
            raise TypeError(
                "warnings must be a tuple."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

        if self.status == ValidationStatus.VALID:
            if not self.valid:
                raise ValueError(
                    "VALID status requires valid=True."
                )

        if self.status == ValidationStatus.INVALID:
            if self.valid:
                raise ValueError(
                    "INVALID status requires valid=False."
                )
