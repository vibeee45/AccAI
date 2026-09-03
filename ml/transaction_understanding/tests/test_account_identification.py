import pytest

from ml.transaction_understanding.account_identification import (
    AccountCatalog,
    AccountIdentificationConfig,
    AccountIdentificationService,
    AccountIdentifier,
    AccountRecord,
    AccountTextFeatures,
)


def create_identifier():
    return AccountIdentifier(
        config=AccountIdentificationConfig(
            top_k=3,
            confidence_threshold=0.50,
        )
    )


def test_default_catalog_is_not_empty():
    catalog = AccountCatalog()

    assert len(catalog) > 0


def test_default_catalog_contains_cash():
    catalog = AccountCatalog()

    account = catalog.get("cash")

    assert account is not None
    assert account.account_name == "Cash"


def test_default_catalog_contains_bank():
    catalog = AccountCatalog()

    account = catalog.get("bank")

    assert account is not None
    assert account.account_name == "Bank"


def test_default_catalog_contains_rent():
    catalog = AccountCatalog()

    account = catalog.get("rent_expense")

    assert account is not None
    assert account.account_name == "Rent Expense"


def test_catalog_rejects_empty():
    with pytest.raises(ValueError):
        AccountCatalog(accounts=())


def test_catalog_rejects_duplicate_ids():
    account_one = AccountRecord(
        account_id="cash",
        account_name="Cash",
        category="asset",
    )

    account_two = AccountRecord(
        account_id="cash",
        account_name="Cash Account",
        category="asset",
    )

    with pytest.raises(ValueError):
        AccountCatalog(
            accounts=(
                account_one,
                account_two,
            )
        )


def test_account_record_requires_id():
    with pytest.raises(ValueError):
        AccountRecord(
            account_id="",
            account_name="Cash",
            category="asset",
        )


def test_account_record_requires_name():
    with pytest.raises(ValueError):
        AccountRecord(
            account_id="cash",
            account_name="",
            category="asset",
        )


def test_config_has_expected_categories():
    config = AccountIdentificationConfig()

    assert "asset" in config.account_categories
    assert "liability" in config.account_categories
    assert "capital" in config.account_categories
    assert "income" in config.account_categories
    assert "expense" in config.account_categories


def test_config_rejects_invalid_top_k():
    with pytest.raises(ValueError):
        AccountIdentificationConfig(
            top_k=0
        )


def test_config_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        AccountIdentificationConfig(
            confidence_threshold=1.5
        )


def test_features_can_fit():
    features = AccountTextFeatures()

    features.fit(
        [
            "cash cash in hand",
            "bank bank account",
            "rent expense office rent",
        ]
    )

    assert features.fitted
    assert features.vocabulary_size() > 0


def test_features_transform():
    features = AccountTextFeatures()

    features.fit(
        [
            "cash cash in hand",
            "bank bank account",
            "rent expense office rent",
        ]
    )

    matrix = features.transform(
        ["office rent"]
    )

    assert matrix.shape[0] == 1
    assert matrix.shape[1] == features.vocabulary_size()


def test_features_require_fit():
    features = AccountTextFeatures()

    with pytest.raises(RuntimeError):
        features.transform(
            ["cash"]
        )


def test_identifier_is_ready():
    identifier = create_identifier()

    assert identifier.vocabulary_size() > 0


def test_identify_rent():
    identifier = create_identifier()

    result = identifier.identify(
        "paid office rent rs 25000",
        transaction_class="rent",
    )

    assert result.selected_account_id == "rent_expense"
    assert result.selected_account_name == "Rent Expense"
    assert result.candidates


def test_identify_salary():
    identifier = create_identifier()

    result = identifier.identify(
        "employee salary paid rs 40000",
        transaction_class="salary",
    )

    assert result.selected_account_id == "salary_expense"


def test_identify_utilities():
    identifier = create_identifier()

    result = identifier.identify(
        "paid electricity bill rs 5000",
        transaction_class="utilities",
    )

    assert result.selected_account_id == "utilities_expense"


def test_identify_transport():
    identifier = create_identifier()

    result = identifier.identify(
        "paid freight and delivery charges rs 5000",
        transaction_class="transport",
    )

    assert result.selected_account_id == "transport_expense"


def test_identify_advertising():
    identifier = create_identifier()

    result = identifier.identify(
        "paid advertising expense rs 10000",
        transaction_class="advertising",
    )

    assert result.selected_account_id == "advertising_expense"


def test_identify_purchase():
    identifier = create_identifier()

    result = identifier.identify(
        "purchased inventory for rs 15000",
        transaction_class="purchase",
    )

    assert result.selected_account_id == "purchases"


def test_identify_sales():
    identifier = create_identifier()

    result = identifier.identify(
        "sold goods to customer for rs 20000",
        transaction_class="sales",
    )

    assert result.selected_account_id == "sales"


def test_identify_capital():
    identifier = create_identifier()

    result = identifier.identify(
        "owner introduced capital rs 100000",
        transaction_class="capital_introduction",
    )

    assert result.selected_account_id == "capital"


def test_identify_loan():
    identifier = create_identifier()

    result = identifier.identify(
        "loan received from bank rs 200000",
        transaction_class="loan",
    )

    assert result.selected_account_id == "loan"


def test_identify_furniture():
    identifier = create_identifier()

    result = identifier.identify(
        "purchased office furniture for rs 50000",
        transaction_class="asset_purchase",
    )

    assert result.selected_account_id == "furniture"


def test_identify_machinery():
    identifier = create_identifier()

    result = identifier.identify(
        "purchased machinery for rs 75000",
        transaction_class="asset_purchase",
    )

    assert result.selected_account_id == "machinery"


def test_identify_computer_equipment():
    identifier = create_identifier()

    result = identifier.identify(
        "bought laptop for office rs 60000",
        transaction_class="asset_purchase",
    )

    assert result.selected_account_id == "computer_equipment"


def test_identify_commission_income():
    identifier = create_identifier()

    result = identifier.identify(
        "commission received rs 5000",
        transaction_class="commission",
    )

    assert result.selected_account_id == "commission_income"


def test_identify_interest_income():
    identifier = create_identifier()

    result = identifier.identify(
        "interest received from bank rs 3000",
        transaction_class="interest",
    )

    assert result.selected_account_id == "interest_income"


def test_identify_tax():
    identifier = create_identifier()

    result = identifier.identify(
        "GST tax paid rs 10000",
        transaction_class="tax",
    )

    assert result.selected_account_id == "tax_expense"


def test_identify_insurance():
    identifier = create_identifier()

    result = identifier.identify(
        "insurance premium paid rs 12000",
        transaction_class="insurance",
    )

    assert result.selected_account_id == "insurance_expense"


def test_identify_returns_ranked_candidates():
    identifier = create_identifier()

    result = identifier.identify(
        "paid office rent rs 25000",
        transaction_class="rent",
    )

    assert len(result.candidates) == 3

    assert result.candidates[0].rank == 1
    assert result.candidates[1].rank == 2
    assert result.candidates[2].rank == 3


def test_candidates_are_sorted_by_score():
    identifier = create_identifier()

    result = identifier.identify(
        "paid office rent rs 25000",
        transaction_class="rent",
    )

    scores = [
        candidate.score
        for candidate in result.candidates
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_selected_account_is_best_candidate():
    identifier = create_identifier()

    result = identifier.identify(
        "paid office rent rs 25000",
        transaction_class="rent",
    )

    assert (
        result.selected_account_id
        == result.candidates[0].account_id
    )


def test_confidence_matches_best_candidate():
    identifier = create_identifier()

    result = identifier.identify(
        "paid rent rs 20000",
        transaction_class="rent",
    )

    assert result.confidence == (
        result.candidates[0].score
    )


def test_confidence_is_between_zero_and_one():
    identifier = create_identifier()

    result = identifier.identify(
        "paid office rent rs 25000",
        transaction_class="rent",
    )

    assert 0 <= result.confidence <= 1


def test_requires_review_is_boolean():
    identifier = create_identifier()

    result = identifier.identify(
        "business transaction",
    )

    assert isinstance(
        result.requires_review,
        bool,
    )


def test_identify_rejects_empty_text():
    identifier = create_identifier()

    with pytest.raises(ValueError):
        identifier.identify("")


def test_identify_rejects_non_string():
    identifier = create_identifier()

    with pytest.raises(TypeError):
        identifier.identify(None)


def test_identify_many():
    identifier = create_identifier()

    results = identifier.identify_many(
        [
            "paid office rent rs 25000",
            "employee salary paid rs 40000",
            "sold goods rs 10000",
        ]
    )

    assert len(results) == 3

    assert results[0].selected_account_id == (
        "rent_expense"
    )

    assert results[1].selected_account_id == (
        "salary_expense"
    )

    assert results[2].selected_account_id == (
        "sales"
    )


def test_identify_many_rejects_empty():
    identifier = create_identifier()

    with pytest.raises(ValueError):
        identifier.identify_many([])


def test_service_is_ready():
    service = AccountIdentificationService()

    assert service.ready is True


def test_service_identifies_account():
    service = AccountIdentificationService()

    result = service.identify(
        "paid office rent rs 25000",
        transaction_class="rent",
    )

    assert result.selected_account_id == (
        "rent_expense"
    )


def test_service_identifies_many():
    service = AccountIdentificationService()

    results = service.identify_many(
        [
            "paid rent rs 25000",
            "paid salary rs 40000",
        ]
    )

    assert len(results) == 2


def test_account_candidate_schema():
    from ml.transaction_understanding.account_identification.schemas import (
        AccountCandidate,
    )

    candidate = AccountCandidate(
        account_id="rent_expense",
        account_name="Rent Expense",
        category="expense",
        score=0.90,
        rank=1,
    )

    assert candidate.account_id == "rent_expense"
    assert candidate.rank == 1


def test_account_candidate_rejects_invalid_score():
    from ml.transaction_understanding.account_identification.schemas import (
        AccountCandidate,
    )

    with pytest.raises(ValueError):
        AccountCandidate(
            account_id="rent_expense",
            account_name="Rent Expense",
            category="expense",
            score=1.5,
            rank=1,
        )


def test_result_schema():
    from ml.transaction_understanding.account_identification.schemas import (
        AccountCandidate,
        AccountIdentificationResult,
    )

    candidate = AccountCandidate(
        account_id="rent_expense",
        account_name="Rent Expense",
        category="expense",
        score=0.90,
        rank=1,
    )

    result = AccountIdentificationResult(
        transaction_text="paid rent",
        candidates=(candidate,),
        selected_account_id="rent_expense",
        selected_account_name="Rent Expense",
        confidence=0.90,
        requires_review=False,
    )

    assert result.selected_account_id == (
        "rent_expense"
    )
