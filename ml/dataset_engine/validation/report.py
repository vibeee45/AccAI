from __future__ import annotations

from collections import Counter

from .schemas import DatasetValidationReport


def summarize_errors(
    report: DatasetValidationReport,
) -> dict[str, int]:
    counter: Counter[str] = Counter()

    for result in report.results:
        for issue in result.issues:
            counter[issue.error_type.value] += 1

    return dict(counter)


def format_report(
    report: DatasetValidationReport,
) -> str:
    lines = [
        "ACCAI Dataset Validation Report",
        "================================",
        f"Rows input:   {report.stats.rows_input}",
        f"Rows valid:   {report.stats.rows_valid}",
        f"Rows invalid: {report.stats.rows_invalid}",
        f"Issues found: {report.stats.issues_found}",
        f"Validation rate: "
        f"{report.stats.validation_rate:.2%}",
    ]

    errors = summarize_errors(report)

    if errors:
        lines.append("")
        lines.append("Errors:")

        for error_type, count in sorted(errors.items()):
            lines.append(
                f"- {error_type}: {count}"
            )

    return "\n".join(lines)
