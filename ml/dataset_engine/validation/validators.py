from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from ..templates import get_template
from .schemas import (
    DatasetValidationReport,
    ValidationErrorType,
    ValidationIssue,
    ValidationResult,
    ValidationStats,
)


_REQUIRED_FIELDS = (
    "transaction_id",
    "date",
    "transaction",
    "amount",
    "template_id",
    "debit_account",
    "credit_account",
    "category",
)


def _get_value(record: Any, field: str):
    if isinstance(record, dict):
        return record.get(field)

    return getattr(record, field, None)


def _validate_required_fields(
    record: Any,
    row_index: int,
) -> list[ValidationIssue]:
    issues = []

    for field in _REQUIRED_FIELDS:
        value = _get_value(record, field)

        if value is None:
            issues.append(
                ValidationIssue(
                    row_index=row_index,
                    error_type=ValidationErrorType.MISSING_FIELD,
                    message=f"Required field '{field}' is missing.",
                )
            )

    return issues


def _validate_date(
    record: Any,
    row_index: int,
) -> list[ValidationIssue]:
    value = _get_value(record, "date")

    if value is None:
        return []

    if isinstance(value, date):
        return []

    issues = [
        ValidationIssue(
            row_index=row_index,
            error_type=ValidationErrorType.INVALID_DATE,
            message="Date must be a datetime.date value.",
        )
    ]

    return issues


def _validate_amount(
    record: Any,
    row_index: int,
) -> list[ValidationIssue]:
    value = _get_value(record, "amount")

    if value is None:
        return []

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return [
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.INVALID_AMOUNT,
                message="Amount must be a valid decimal number.",
            )
        ]

    if amount <= Decimal("0"):
        return [
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.INVALID_AMOUNT,
                message="Amount must be greater than zero.",
            )
        ]

    return []


def _validate_transaction(
    record: Any,
    row_index: int,
) -> list[ValidationIssue]:
    value = _get_value(record, "transaction")

    if value is None:
        return []

    if not str(value).strip():
        return [
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.EMPTY_TRANSACTION,
                message="Transaction text cannot be empty.",
            )
        ]

    return []


def _validate_template(
    record: Any,
    row_index: int,
) -> list[ValidationIssue]:
    template_id = _get_value(record, "template_id")

    if not template_id:
        return []

    try:
        template = get_template(str(template_id))
    except KeyError:
        return [
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.INVALID_TEMPLATE,
                message=f"Unknown template: {template_id}.",
            )
        ]

    debit = _get_value(record, "debit_account")
    credit = _get_value(record, "credit_account")

    issues = []

    if debit and str(debit) != template.debit_account:
        issues.append(
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.TEMPLATE_MISMATCH,
                message=(
                    f"Debit account '{debit}' does not match "
                    f"template debit account '{template.debit_account}'."
                ),
            )
        )

    if credit and str(credit) != template.credit_account:
        issues.append(
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.TEMPLATE_MISMATCH,
                message=(
                    f"Credit account '{credit}' does not match "
                    f"template credit account '{template.credit_account}'."
                ),
            )
        )

    return issues


def _validate_accounts(
    record: Any,
    row_index: int,
) -> list[ValidationIssue]:
    debit = _get_value(record, "debit_account")
    credit = _get_value(record, "credit_account")

    issues = []

    if debit is not None and not str(debit).strip():
        issues.append(
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.INVALID_DEBIT_ACCOUNT,
                message="Debit account cannot be empty.",
            )
        )

    if credit is not None and not str(credit).strip():
        issues.append(
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.INVALID_CREDIT_ACCOUNT,
                message="Credit account cannot be empty.",
            )
        )

    if (
        debit is not None
        and credit is not None
        and str(debit).strip()
        and str(credit).strip()
        and str(debit).strip().lower()
        == str(credit).strip().lower()
    ):
        issues.append(
            ValidationIssue(
                row_index=row_index,
                error_type=ValidationErrorType.SAME_DEBIT_CREDIT,
                message="Debit and credit accounts cannot be identical.",
            )
        )

    return issues


def validate_record(
    record: Any,
    row_index: int = 0,
) -> ValidationResult:
    issues: list[ValidationIssue] = []

    issues.extend(
        _validate_required_fields(record, row_index)
    )
    issues.extend(
        _validate_transaction(record, row_index)
    )
    issues.extend(
        _validate_date(record, row_index)
    )
    issues.extend(
        _validate_amount(record, row_index)
    )
    issues.extend(
        _validate_accounts(record, row_index)
    )
    issues.extend(
        _validate_template(record, row_index)
    )

    result = ValidationResult(
        row_index=row_index,
        valid=not issues,
        issues=tuple(issues),
    )

    result.validate()

    return result


def validate_dataset(
    records: list[Any] | tuple[Any, ...],
) -> DatasetValidationReport:
    results: list[ValidationResult] = []
    seen_ids: set[str] = set()

    for index, record in enumerate(records):
        result = validate_record(record, index)

        issues = list(result.issues)

        transaction_id = _get_value(
            record,
            "transaction_id",
        )

        if transaction_id is not None:
            normalized_id = str(transaction_id).strip()

            if normalized_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        row_index=index,
                        error_type=ValidationErrorType.DUPLICATE_ID,
                        message=(
                            f"Duplicate transaction ID: "
                            f"{normalized_id}."
                        ),
                    )
                )

            seen_ids.add(normalized_id)

        result = ValidationResult(
            row_index=index,
            valid=not issues,
            issues=tuple(issues),
        )

        result.validate()
        results.append(result)

    valid_count = sum(
        result.valid
        for result in results
    )

    invalid_count = len(results) - valid_count

    issue_count = sum(
        len(result.issues)
        for result in results
    )

    stats = ValidationStats(
        rows_input=len(results),
        rows_valid=valid_count,
        rows_invalid=invalid_count,
        issues_found=issue_count,
    )

    return DatasetValidationReport(
        results=tuple(results),
        stats=stats,
    )
