from pathlib import Path

import pandas as pd
import pytest

from ml.dataset_engine.cleaning import (
    CleaningConfig,
    CleaningError,
    CleaningResult,
    clean_csv,
    clean_dataframe,
)
from ml.dataset_engine.cleaning.cleaner import (
    normalize_column_name,
    normalize_transaction_text,
    parse_amount,
)


def test_normalize_column_name():
    assert normalize_column_name("Transaction Date") == "transaction_date"
    assert normalize_column_name(" Amount ") == "amount"
    assert normalize_column_name("Amount (INR)") == "amount_inr"


def test_normalize_column_name_special_characters():
    assert normalize_column_name(
        "Transaction---Details!!!"
    ) == "transaction_details"


def test_normalize_transaction_text():
    assert normalize_transaction_text(
        "   Cash    Sale   "
    ) == "Cash Sale"


def test_normalize_transaction_text_line_breaks():
    assert normalize_transaction_text(
        "Cash\nSale\tReceived"
    ) == "Cash Sale Received"


def test_normalize_transaction_text_none():
    assert normalize_transaction_text(None) == ""


def test_normalize_transaction_text_nan():
    assert normalize_transaction_text(float("nan")) == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1000, 1000.0),
        ("1000", 1000.0),
        ("1,000", 1000.0),
        ("₹1,000", 1000.0),
        ("Rs. 1,000", 1000.0),
        ("$1,000", 1000.0),
        ("(1,000)", -1000.0),
        ("-1000", -1000.0),
        (" 2500 ", 2500.0),
    ],
)
def test_parse_amount(value, expected):
    assert parse_amount(value) == expected


def test_parse_invalid_amount():
    assert pd.isna(parse_amount("not-a-number"))


def test_parse_empty_amount():
    assert pd.isna(parse_amount(""))


def test_parse_none_amount():
    assert pd.isna(parse_amount(None))


def test_clean_dataframe_returns_result():
    dataframe = pd.DataFrame(
        {
            "Date": ["2026-01-01"],
            "Transaction": ["  Cash Sale  "],
            "Amount": ["1,000"],
        }
    )

    result = clean_dataframe(dataframe)

    assert isinstance(result, CleaningResult)


def test_clean_dataframe_normalizes_columns():
    dataframe = pd.DataFrame(
        {
            "Transaction Date": ["2026-01-01"],
            "Transaction Description": ["Cash Sale"],
            "Amount (INR)": ["1000"],
        }
    )

    result = clean_dataframe(dataframe)

    assert list(result.dataframe.columns) == [
        "date",
        "transaction",
        "amount",
    ]


def test_clean_dataframe_normalizes_text():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": [
                "   Cash    Sale   Received   "
            ],
            "amount": [1000],
        }
    )

    result = clean_dataframe(dataframe)

    assert result.dataframe.loc[
        0,
        "transaction",
    ] == "Cash Sale Received"


def test_clean_dataframe_converts_dates():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-02-15",
            ],
            "transaction": [
                "Cash Sale",
                "Purchase",
            ],
            "amount": [
                1000,
                500,
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert pd.api.types.is_datetime64_any_dtype(
        result.dataframe["date"]
    )


def test_clean_dataframe_converts_amounts():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
            ],
            "transaction": [
                "Cash Sale",
                "Purchase",
            ],
            "amount": [
                "1,000",
                "₹500",
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert result.dataframe["amount"].tolist() == [
        1000.0,
        500.0,
    ]


def test_invalid_date_removed():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "not-a-date",
            ],
            "transaction": [
                "Cash Sale",
                "Purchase",
            ],
            "amount": [
                1000,
                500,
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert len(result.dataframe) == 1
    assert result.stats.invalid_date_rows_removed == 1


def test_invalid_amount_removed():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
            ],
            "transaction": [
                "Cash Sale",
                "Purchase",
            ],
            "amount": [
                1000,
                "invalid",
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert len(result.dataframe) == 1
    assert result.stats.invalid_amount_rows_removed == 1


def test_empty_transaction_removed():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
            ],
            "transaction": [
                "Cash Sale",
                "   ",
            ],
            "amount": [
                1000,
                500,
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert len(result.dataframe) == 1
    assert result.stats.empty_transaction_rows_removed == 1


def test_duplicate_rows_removed():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-01",
                "2026-01-02",
            ],
            "transaction": [
                "Cash Sale",
                "Cash Sale",
                "Purchase",
            ],
            "amount": [
                1000,
                1000,
                500,
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert len(result.dataframe) == 2
    assert result.stats.duplicate_rows_removed == 1


def test_duplicate_removal_can_be_disabled():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-01",
            ],
            "transaction": [
                "Cash Sale",
                "Cash Sale",
            ],
            "amount": [
                1000,
                1000,
            ],
        }
    )

    result = clean_dataframe(
        dataframe,
        CleaningConfig(drop_duplicates=False),
    )

    assert len(result.dataframe) == 2
    assert result.stats.duplicate_rows_removed == 0


def test_zero_amount_allowed_by_default():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": ["Adjustment"],
            "amount": [0],
        }
    )

    result = clean_dataframe(dataframe)

    assert len(result.dataframe) == 1


def test_zero_amount_can_be_rejected():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": ["Adjustment"],
            "amount": [0],
        }
    )

    result = clean_dataframe(
        dataframe,
        CleaningConfig(allow_zero_amount=False),
    )

    assert len(result.dataframe) == 0


def test_negative_amount_allowed_by_default():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": ["Refund"],
            "amount": [-500],
        }
    )

    result = clean_dataframe(dataframe)

    assert len(result.dataframe) == 1
    assert result.dataframe.loc[0, "amount"] == -500


def test_negative_amount_can_be_rejected():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": ["Refund"],
            "amount": [-500],
        }
    )

    result = clean_dataframe(
        dataframe,
        CleaningConfig(allow_negative_amount=False),
    )

    assert len(result.dataframe) == 0


def test_missing_required_column_raises_error():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": ["Cash Sale"],
        }
    )

    with pytest.raises(CleaningError):
        clean_dataframe(dataframe)


def test_missing_date_column_raises_error():
    dataframe = pd.DataFrame(
        {
            "transaction": ["Cash Sale"],
            "amount": [1000],
        }
    )

    with pytest.raises(CleaningError):
        clean_dataframe(dataframe)


def test_missing_transaction_column_raises_error():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "amount": [1000],
        }
    )

    with pytest.raises(CleaningError):
        clean_dataframe(dataframe)


def test_missing_amount_column_raises_error():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "transaction": ["Cash Sale"],
        }
    )

    with pytest.raises(CleaningError):
        clean_dataframe(dataframe)


def test_empty_dataframe_raises_error():
    dataframe = pd.DataFrame(
        columns=[
            "date",
            "transaction",
            "amount",
        ]
    )

    with pytest.raises(CleaningError):
        clean_dataframe(dataframe)


def test_cleaning_does_not_modify_original():
    dataframe = pd.DataFrame(
        {
            "Date": ["2026-01-01"],
            "Transaction": ["   Cash Sale   "],
            "Amount": ["1,000"],
        }
    )

    original = dataframe.copy(deep=True)

    clean_dataframe(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_cleaning_statistics():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
                "invalid",
                "2026-01-01",
            ],
            "transaction": [
                "Cash Sale",
                "Purchase",
                "Expense",
                "Cash Sale",
            ],
            "amount": [
                1000,
                "invalid",
                500,
                1000,
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert result.stats.rows_input == 4
    assert result.stats.rows_output == 1
    assert result.stats.rows_removed == 3

    assert result.stats.invalid_date_rows_removed == 1
    assert result.stats.invalid_amount_rows_removed == 1
    assert result.stats.duplicate_rows_removed == 1


def test_retention_rate():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
            ],
            "transaction": [
                "Cash Sale",
                "Purchase",
            ],
            "amount": [
                1000,
                "invalid",
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert result.stats.retention_rate == 0.5


def test_empty_input_retention_rate():
    from ml.dataset_engine.cleaning.schemas import CleaningStats

    stats = CleaningStats(
        rows_input=0,
        rows_output=0,
        rows_removed=0,
        duplicate_rows_removed=0,
        empty_transaction_rows_removed=0,
        invalid_date_rows_removed=0,
        invalid_amount_rows_removed=0,
    )

    assert stats.retention_rate == 0.0


def test_clean_csv(tmp_path: Path):
    input_path = tmp_path / "raw.csv"
    output_path = tmp_path / "cleaned" / "clean.csv"

    dataframe = pd.DataFrame(
        {
            "Date": ["2026-01-01"],
            "Transaction": ["  Cash Sale  "],
            "Amount": ["1,000"],
        }
    )

    dataframe.to_csv(
        input_path,
        index=False,
    )

    result = clean_csv(
        input_path,
        output_path,
    )

    assert output_path.is_file()
    assert len(result.dataframe) == 1

    saved = pd.read_csv(output_path)

    assert list(saved.columns) == [
        "date",
        "transaction",
        "amount",
    ]

    assert saved.loc[
        0,
        "transaction",
    ] == "Cash Sale"

    assert saved.loc[
        0,
        "amount",
    ] == 1000.0


def test_clean_csv_missing_input_fails(
    tmp_path: Path,
):
    with pytest.raises(CleaningError):
        clean_csv(
            tmp_path / "missing.csv",
            tmp_path / "cleaned.csv",
        )


def test_end_to_end_cleaning():
    dataframe = pd.DataFrame(
        {
            "Transaction Date": [
                "2026-01-01",
                "2026-01-02",
            ],
            "Transaction Description": [
                "   Cash Sale   ",
                "Office    Expense",
            ],
            "Amount (INR)": [
                "₹1,000",
                "2,500",
            ],
        }
    )

    result = clean_dataframe(dataframe)

    cleaned = result.dataframe

    assert list(cleaned.columns) == [
        "date",
        "transaction",
        "amount",
    ]

    assert cleaned["transaction"].tolist() == [
        "Cash Sale",
        "Office Expense",
    ]

    assert cleaned["amount"].tolist() == [
        1000.0,
        2500.0,
    ]

    assert pd.api.types.is_datetime64_any_dtype(
        cleaned["date"]
    )


def test_cleaning_preserves_row_order():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
                "2026-01-03",
            ],
            "transaction": [
                "First",
                "Second",
                "Third",
            ],
            "amount": [
                100,
                200,
                300,
            ],
        }
    )

    result = clean_dataframe(dataframe)

    assert result.dataframe[
        "transaction"
    ].tolist() == [
        "First",
        "Second",
        "Third",
    ]
