from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class ValidationErrorType(str, Enum):
    MISSING_FIELD = "missing_field"
    INVALID_DATE = "invalid_date"
    INVALID_AMOUNT = "invalid_amount"
    EMPTY_TRANSACTION = "empty_transaction"
    INVALID_TEMPLATE = "invalid_template"
    INVALID_DEBIT_ACCOUNT = "invalid_debit_account"
    INVALID_CREDIT_ACCOUNT = "invalid_credit_account"
    SAME_DEBIT_CREDIT = "same_debit_credit"
    TEMPLATE_MISMATCH = "template_mismatch"
    DUPLICATE_ID = "duplicate_id"


@dataclass(frozen=True)
class ValidationIssue:
    row_index: int
    error_type: ValidationErrorType
    message: str

    def validate(self) -> None:
        if self.row_index < 0:
            raise ValueError("row_index cannot be negative")

        if not self.message.strip():
            raise ValueError("message cannot be empty")


@dataclass(frozen=True)
class ValidationResult:
    row_index: int
    valid: bool
    issues: tuple[ValidationIssue, ...]

    def validate(self) -> None:
        if self.row_index < 0:
            raise ValueError("row_index cannot be negative")

        if self.valid and self.issues:
            raise ValueError(
                "A valid row cannot contain validation issues"
            )


@dataclass(frozen=True)
class ValidationStats:
    rows_input: int
    rows_valid: int
    rows_invalid: int
    issues_found: int

    @property
    def validation_rate(self) -> float:
        if self.rows_input == 0:
            return 0.0

        return self.rows_valid / self.rows_input


@dataclass(frozen=True)
class DatasetValidationReport:
    results: tuple[ValidationResult, ...]
    stats: ValidationStats

    @property
    def valid(self) -> bool:
        return self.stats.rows_invalid == 0

    @property
    def invalid_rows(self) -> tuple[ValidationResult, ...]:
        return tuple(
            result
            for result in self.results
            if not result.valid
        )
