import pytest

from ml.transaction_understanding.preprocessing import (
    PreprocessingConfig,
    TransactionPreprocessor,
    preprocess_transaction,
    preprocess_transactions,
)


def test_lowercase_and_whitespace():
    result = preprocess_transaction("  PAID    Office Rent   ")

    assert result == "paid office rent"


def test_indian_currency_normalization():
    assert preprocess_transaction("Paid \u20b9 5,000 to Ramesh") == (
        "paid rs 5,000 to ramesh"
    )

    assert preprocess_transaction("Paid Rs. 5000 to Ramesh") == (
        "paid rs 5000 to ramesh"
    )

    assert preprocess_transaction("Paid INR 5000 to Ramesh") == (
        "paid rs 5000 to ramesh"
    )


def test_currency_symbols():
    assert preprocess_transaction("Received $500") == "received usd 500"
    assert preprocess_transaction("Received \u20ac500") == "received eur 500"
    assert preprocess_transaction("Received \u00a3500") == "received gbp 500"


def test_accounting_abbreviations():
    result = preprocess_transaction(
        "Paid pur exp through acct"
    )

    assert result == "paid purchase expense through account"


def test_unicode_normalization():
    result = preprocess_transaction("Paid Caf\u00e9 expenses")

    assert result == "paid caf\u00e9 expenses"


def test_amount_is_preserved():
    result = preprocess_transaction(
        "Purchased goods for \u20b91,25,000.50"
    )

    assert "1,25,000.50" in result
    assert "12500050" not in result


def test_punctuation_normalization():
    result = preprocess_transaction(
        "Paid: office-rent!!! \u20b95,000."
    )

    assert result == "paid office-rent rs 5,000."


def test_batch_processing():
    result = preprocess_transactions(
        [
            "Paid \u20b9500 rent",
            "Received Rs. 1,000 cash",
            "Purchased goods for INR 2,000",
        ]
    )

    assert result == (
        "paid rs 500 rent",
        "received rs 1,000 cash",
        "purchased goods for rs 2,000",
    )


def test_batch_result_contains_original_text():
    processor = TransactionPreprocessor()

    result = processor.preprocess_batch(
        ["Paid \u20b9500 rent"]
    )

    assert result.items[0].original_text == "Paid \u20b9500 rent"
    assert result.items[0].normalized_text == "paid rs 500 rent"


def test_deterministic_output():
    processor = TransactionPreprocessor()

    text = "Paid \u20b9 5,000 to Ramesh for Office Rent."

    first = processor.preprocess(text)
    second = processor.preprocess(text)

    assert first == second


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        preprocess_transaction("")


def test_whitespace_only_text_rejected():
    with pytest.raises(ValueError):
        preprocess_transaction("     ")


def test_none_rejected():
    with pytest.raises(ValueError):
        preprocess_transaction(None)


def test_non_string_rejected():
    with pytest.raises(TypeError):
        preprocess_transaction(5000)


def test_configuration_can_disable_lowercase():
    processor = TransactionPreprocessor(
        PreprocessingConfig(lowercase=False)
    )

    result = processor.preprocess("PAID \u20b9500")

    assert result.normalized_text == "PAID rs 500"


def test_configuration_can_disable_currency_normalization():
    processor = TransactionPreprocessor(
        PreprocessingConfig(normalize_currency=False)
    )

    result = processor.preprocess("Paid \u20b9500")

    assert result.normalized_text == "paid \u20b9500"


def test_public_batch_api():
    result = preprocess_transactions(
        ("Paid rent", "Received cash")
    )

    assert result == (
        "paid rent",
        "received cash",
    )
