import pytest

from ml.transaction_understanding.entity_extraction import (
    EntityExtractionConfig,
    EntityType,
    TransactionEntityExtractor,
    extract_entities,
    extract_entities_batch,
)


def entities_of_type(result, entity_type):
    return [
        entity
        for entity in result.entities
        if entity.entity_type == entity_type
    ]


def test_extract_amount():
    result = extract_entities(
        "paid rs 5000 for office rent"
    )

    amounts = entities_of_type(result, EntityType.AMOUNT)

    assert len(amounts) == 1
    assert amounts[0].text == "5000"
    assert amounts[0].normalized_value == "5000"


def test_extract_indian_amount():
    result = extract_entities(
        "purchased goods for rs 1,25,000.50"
    )

    amounts = entities_of_type(result, EntityType.AMOUNT)

    assert len(amounts) == 1
    assert amounts[0].text == "1,25,000.50"
    assert amounts[0].normalized_value == "125000.50"


def test_extract_currency():
    result = extract_entities(
        "paid rs 5000"
    )

    currencies = entities_of_type(result, EntityType.CURRENCY)

    assert len(currencies) == 1
    assert currencies[0].normalized_value == "INR"


def test_extract_date():
    result = extract_entities(
        "paid rs 5000 on 12/08/2026"
    )

    dates = entities_of_type(result, EntityType.DATE)

    assert len(dates) == 1
    assert dates[0].text == "12/08/2026"


def test_extract_iso_date():
    result = extract_entities(
        "paid rs 5000 on 2026-08-12"
    )

    dates = entities_of_type(result, EntityType.DATE)

    assert len(dates) == 1
    assert dates[0].text == "2026-08-12"


def test_extract_upi():
    result = extract_entities(
        "paid rs 5000 to ramesh through upi"
    )

    payments = entities_of_type(
        result,
        EntityType.PAYMENT_REFERENCE,
    )

    assert len(payments) == 1
    assert payments[0].normalized_value == "upi"


def test_extract_multiple_payment_modes():
    result = extract_entities(
        "paid rs 5000 through neft and rs 2000 through cash"
    )

    payments = entities_of_type(
        result,
        EntityType.PAYMENT_REFERENCE,
    )

    values = {entity.normalized_value for entity in payments}

    assert "neft" in values
    assert "cash" in values


def test_extract_person():
    result = extract_entities(
        "paid rs 5000 to Ramesh Kumar"
    )

    people = entities_of_type(result, EntityType.PERSON)

    assert len(people) == 1
    assert people[0].normalized_value == "ramesh kumar"


def test_extract_organization():
    result = extract_entities(
        "paid rs 5000 to ABC Technologies Pvt Ltd"
    )

    organizations = entities_of_type(
        result,
        EntityType.ORGANIZATION,
    )

    assert len(organizations) == 1
    assert "abc technologies" in organizations[0].normalized_value


def test_extract_description():
    result = extract_entities(
        "paid rs 5000 for office rent through upi"
    )

    descriptions = entities_of_type(
        result,
        EntityType.DESCRIPTION,
    )

    assert len(descriptions) == 1
    assert descriptions[0].normalized_value == "office rent"


def test_extract_account_reference():
    result = extract_entities(
        "paid rs 5000 from account no 123456"
    )

    accounts = entities_of_type(
        result,
        EntityType.ACCOUNT_REFERENCE,
    )

    assert len(accounts) == 1
    assert "123456" in accounts[0].text


def test_complete_transaction():
    result = extract_entities(
        "Paid rs 5,000 to Ramesh Kumar for office rent "
        "through UPI on 12/08/2026"
    )

    assert entities_of_type(result, EntityType.AMOUNT)
    assert entities_of_type(result, EntityType.CURRENCY)
    assert entities_of_type(result, EntityType.PERSON)
    assert entities_of_type(result, EntityType.DESCRIPTION)
    assert entities_of_type(result, EntityType.PAYMENT_REFERENCE)
    assert entities_of_type(result, EntityType.DATE)


def test_original_text_preserved():
    text = "Paid rs 5000 to Ramesh"

    result = extract_entities(text)

    assert result.original_text == text


def test_entities_have_valid_spans():
    text = "paid rs 5000 to Ramesh for rent"

    result = extract_entities(text)

    for entity in result.entities:
        assert 0 <= entity.start < entity.end <= len(text)
        assert text[entity.start:entity.end] == entity.text


def test_confidence_is_valid():
    result = extract_entities(
        "paid rs 5000 through upi"
    )

    for entity in result.entities:
        assert 0.0 <= entity.confidence <= 1.0


def test_batch_extraction():
    results = extract_entities_batch(
        [
            "paid rs 500 rent",
            "received rs 1000 through upi",
        ]
    )

    assert len(results) == 2

    assert entities_of_type(
        results[0],
        EntityType.AMOUNT,
    )

    assert entities_of_type(
        results[1],
        EntityType.PAYMENT_REFERENCE,
    )


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        extract_entities("")


def test_none_rejected():
    with pytest.raises(ValueError):
        extract_entities(None)


def test_non_string_rejected():
    with pytest.raises(TypeError):
        extract_entities(5000)


def test_config_can_disable_amounts():
    extractor = TransactionEntityExtractor(
        EntityExtractionConfig(extract_amounts=False)
    )

    result = extractor.extract("paid rs 5000")

    assert not entities_of_type(
        result,
        EntityType.AMOUNT,
    )


def test_deterministic_extraction():
    text = (
        "Paid rs 5,000 to Ramesh Kumar "
        "for office rent through UPI"
    )

    first = extract_entities(text)
    second = extract_entities(text)

    assert first == second
