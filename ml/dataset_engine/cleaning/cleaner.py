
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .schemas import CleaningConfig, CleaningStats


class CleaningError(RuntimeError):
    """Raised when the dataset cannot be cleaned safely."""


@dataclass(frozen=True)
class CleaningResult:
    dataframe: pd.DataFrame
    stats: CleaningStats


_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "date": (
        "date",
        "transaction_date",
        "transactiondate",
        "entry_date",
        "entrydate",
    ),
    "transaction": (
        "transaction",
        "description",
        "narration",
        "particulars",
        "details",
        "transaction_description",
        "transactiondetails",
    ),
    "amount": (
        "amount",
        "value",
        "transaction_amount",
        "transaction_value",
        "amount_inr",
        "amount_rs",
        "amount_rupees",
    ),
}


def normalize_column_name(column: Any) -> str:
    """Normalize a column name into snake_case."""

    value = str(column).strip().lower()

    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def normalize_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return a copy with normalized column names."""

    result = dataframe.copy()

    result.columns = [
        normalize_column_name(column)
        for column in result.columns
    ]

    return result


def resolve_required_columns(
    dataframe: pd.DataFrame,
    config: CleaningConfig | None = None,
) -> pd.DataFrame:
    """Resolve recognized aliases to ACCAI canonical columns."""

    config = config or CleaningConfig()

    result = dataframe.copy()

    existing = {
        normalize_column_name(column): column
        for column in result.columns
    }

    rename_map: dict[Any, str] = {}

    for canonical in config.required_columns:
        aliases = _COLUMN_ALIASES.get(
            canonical,
            (canonical,),
        )

        found_column = None

        for alias in aliases:
            normalized_alias = normalize_column_name(alias)

            if normalized_alias in existing:
                found_column = existing[normalized_alias]
                break

        if found_column is None:
            raise CleaningError(
                f"Required column '{canonical}' was not found. "
                f"Available columns: {list(result.columns)}"
            )

        rename_map[found_column] = canonical

    return result.rename(columns=rename_map)


def normalize_transaction_text(
    value: Any,
) -> str:
    """Normalize transaction text without changing its meaning."""

    if pd.isna(value):
        return ""

    text = str(value)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_amount(value: Any) -> float:
    """
    Convert common accounting amount formats to float.

    Supported examples:

        1000
        "1000"
        "1,000"
        "₹1,000"
        "Rs. 1,000"
        "Rs 1,000"
        "$1,000"
        "(1,000)"
        "-1000"

    Parentheses represent negative amounts.
    """

    if pd.isna(value):
        return float("nan")

    if isinstance(value, bool):
        return float("nan")

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return float("nan")

    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    # Remove common currency prefixes/symbols.
    text = re.sub(
        r"(?i)^rs\.?\s*",
        "",
        text,
    )

    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")

    # Remove thousands separators.
    text = text.replace(",", "")

    text = text.strip()

    try:
        amount = float(text)
    except (TypeError, ValueError):
        return float("nan")

    if negative:
        amount = -abs(amount)

    return amount


def normalize_dates(
    series: pd.Series,
) -> pd.Series:
    """Parse dates. Invalid values become NaT."""

    return pd.to_datetime(
        series,
        errors="coerce",
    )


def clean_dataframe(
    dataframe: pd.DataFrame,
    config: CleaningConfig | None = None,
) -> CleaningResult:
    """
    Clean a raw accounting dataframe.

    Raw input is never modified in place.
    """

    config = config or CleaningConfig()

    if not isinstance(dataframe, pd.DataFrame):
        raise CleaningError(
            "clean_dataframe expects a pandas DataFrame."
        )

    rows_input = len(dataframe)

    if rows_input == 0:
        raise CleaningError(
            "Cannot clean an empty dataframe."
        )

    result = normalize_columns(dataframe)

    result = resolve_required_columns(
        result,
        config=config,
    )

    result = result.loc[
        :,
        list(config.required_columns),
    ].copy()

    # ---------------------------------------------------------------
    # Transaction text
    # ---------------------------------------------------------------

    if config.normalize_text:
        result["transaction"] = result[
            "transaction"
        ].map(normalize_transaction_text)

    # ---------------------------------------------------------------
    # Dates
    # ---------------------------------------------------------------

    result["date"] = normalize_dates(
        result["date"]
    )

    invalid_date_mask = result["date"].isna()

    invalid_date_rows_removed = int(
        invalid_date_mask.sum()
    )

    if config.drop_invalid_dates:
        result = result.loc[
            ~invalid_date_mask
        ].copy()

    # ---------------------------------------------------------------
    # Amounts
    # ---------------------------------------------------------------

    result["amount"] = result["amount"].map(
        parse_amount
    )

    invalid_amount_mask = result["amount"].isna()

    invalid_amount_rows_removed = int(
        invalid_amount_mask.sum()
    )

    if config.drop_invalid_amounts:
        result = result.loc[
            ~invalid_amount_mask
        ].copy()

    # ---------------------------------------------------------------
    # Empty transaction descriptions
    # ---------------------------------------------------------------

    empty_transaction_mask = (
        result["transaction"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
    )

    empty_transaction_rows_removed = int(
        empty_transaction_mask.sum()
    )

    if config.drop_empty_transactions:
        result = result.loc[
            ~empty_transaction_mask
        ].copy()

    # ---------------------------------------------------------------
    # Amount rules
    # ---------------------------------------------------------------

    if not config.allow_zero_amount:
        result = result.loc[
            result["amount"] != 0
        ].copy()

    if not config.allow_negative_amount:
        result = result.loc[
            result["amount"] >= 0
        ].copy()

    # ---------------------------------------------------------------
    # Duplicate removal
    # ---------------------------------------------------------------

    duplicate_rows_removed = 0

    if config.drop_duplicates:
        before_duplicates = len(result)

        result = result.drop_duplicates(
            keep="first"
        ).copy()

        duplicate_rows_removed = (
            before_duplicates - len(result)
        )

    # ---------------------------------------------------------------
    # Final cleanup
    # ---------------------------------------------------------------

    if config.strip_whitespace:
        result["transaction"] = (
            result["transaction"]
            .astype(str)
            .str.strip()
        )

    result = result.reset_index(drop=True)

    rows_output = len(result)

    rows_removed = rows_input - rows_output

    stats = CleaningStats(
        rows_input=rows_input,
        rows_output=rows_output,
        rows_removed=rows_removed,
        duplicate_rows_removed=duplicate_rows_removed,
        empty_transaction_rows_removed=(
            empty_transaction_rows_removed
        ),
        invalid_date_rows_removed=(
            invalid_date_rows_removed
        ),
        invalid_amount_rows_removed=(
            invalid_amount_rows_removed
        ),
    )

    return CleaningResult(
        dataframe=result,
        stats=stats,
    )


def clean_csv(
    input_path: str | Path,
    output_path: str | Path,
    config: CleaningConfig | None = None,
) -> CleaningResult:
    """Clean a CSV and write the cleaned dataset."""

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise CleaningError(
            f"Input dataset does not exist: {input_path}"
        )

    try:
        dataframe = pd.read_csv(input_path)
    except Exception as exc:
        raise CleaningError(
            f"Unable to read CSV dataset: {input_path}"
        ) from exc

    result = clean_dataframe(
        dataframe,
        config=config,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.dataframe.to_csv(
        output_path,
        index=False,
    )

    return result
