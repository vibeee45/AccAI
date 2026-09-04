from decimal import Decimal

import pytest

from ml.transaction_understanding.accounting_adapter import (
    AccountingAccount,
    AccountingTransaction,
)

from ml.transaction_understanding.rule_validation import (
    AccountingRuleValidator,
    RuleValidationConfig,
    RuleValidationResult,
    RuleValidationService,
    ValidationIssue,
    ValidationSeverity,
    ValidationStatus,
)


def make_transaction(
    amount=Decimal("1000.00"),
    confidence=0.96,
    requires_review=False,
):
    return AccountingTransaction(
        transaction_id="txn-001",
        description="cash sale",
        amount=amount,
        debit_account=AccountingAccount(
            "cash",
            "Cash",
        ),
        credit_account=AccountingAccount(
            "sales",
            "Sales",
        ),
        transaction_class="sales",
        payment_mode="cash",
        ai_confidence=confidence,
        requires_review=requires_review,
        source_text="cash sale",
        normalized_text="cash sale",
        metadata={
            "source": "excel",
            "row": 5,
        },
    )


def test_config_defaults():
    config = RuleValidationConfig()

    assert config.require_distinct_accounts is True
    assert config.require_positive_amount is True
    assert config.require_balanced_entry is True
    assert config.confidence_threshold == 0.80


def test_config_custom_values():
    config = RuleValidationConfig(
        require_distinct_accounts=False,
        require_positive_amount=False,
        require_balanced_entry=False,
        confidence_threshold=0.70,
    )

    assert config.require_distinct_accounts is False
    assert config.require_positive_amount is False
    assert config.require_balanced_entry is False
    assert config.confidence_threshold == 0.70


def test_config_rejects_invalid_boolean():
    with pytest.raises(TypeError):
        RuleValidationConfig(
            require_distinct_accounts="yes"
        )


def test_config_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        RuleValidationConfig(
            confidence_threshold=1.5
        )


def test_validation_issue_requires_code():
    with pytest.raises(ValueError):
        ValidationIssue(
            code="",
            message="test",
            severity=ValidationSeverity.ERROR,
        )


def test_validation_issue_requires_message():
    with pytest.raises(ValueError):
        ValidationIssue(
            code="TEST",
            message="",
            severity=ValidationSeverity.ERROR,
        )


def test_validation_result_valid():
    result = RuleValidationResult(
        status=ValidationStatus.VALID,
        valid=True,
    )

    assert result.valid is True
    assert result.status == ValidationStatus.VALID


def test_validation_result_invalid_requires_false():
    with pytest.raises(ValueError):
        RuleValidationResult(
            status=ValidationStatus.INVALID,
            valid=True,
        )


def test_validation_result_valid_requires_true():
    with pytest.raises(ValueError):
        RuleValidationResult(
            status=ValidationStatus.VALID,
            valid=False,
        )


def test_validation_result_confidence_range():
    with pytest.raises(ValueError):
        RuleValidationResult(
            status=ValidationStatus.VALID,
            valid=True,
            confidence=1.5,
        )


def test_validator_success():
    result = AccountingRuleValidator().validate(
        make_transaction()
    )

    assert result.valid is True
    assert result.status == ValidationStatus.VALID
    assert result.issues == ()
    assert result.warnings == ()


def test_validator_returns_confidence():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.91
        )
    )

    assert result.confidence == 0.91


def test_validator_metadata_contains_transaction_id():
    result = AccountingRuleValidator().validate(
        make_transaction()
    )

    assert (
        result.metadata["transaction_id"]
        == "txn-001"
    )


def test_negative_amount_is_invalid():
    with pytest.raises(ValueError):
        make_transaction(
            Decimal("-100")
        )


def test_zero_amount_is_invalid():
    with pytest.raises(ValueError):
        make_transaction(
            Decimal("0")
        )


def test_same_accounts_are_rejected():
    with pytest.raises(ValueError):
        AccountingTransaction(
            transaction_id="txn-invalid",
            description="invalid transaction",
            amount=Decimal("1000"),
            debit_account=AccountingAccount(
                "cash",
                "Cash",
            ),
            credit_account=AccountingAccount(
                "cash",
                "Cash",
            ),
            transaction_class="sales",
            payment_mode="cash",
            ai_confidence=0.95,
            requires_review=False,
            source_text="invalid",
            normalized_text="invalid",
        )


def test_invalid_input_type():
    with pytest.raises(TypeError):
        AccountingRuleValidator().validate(
            "invalid"
        )


def test_low_confidence_requires_review():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.50
        )
    )

    assert result.valid is True
    assert (
        result.status
        == ValidationStatus.REVIEW_REQUIRED
    )

    assert any(
        issue.code == "LOW_AI_CONFIDENCE"
        for issue in result.warnings
    )


def test_exact_threshold_is_accepted():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.80
        )
    )

    assert result.status == ValidationStatus.VALID


def test_requires_review_flag_creates_warning():
    result = AccountingRuleValidator().validate(
        make_transaction(
            requires_review=True
        )
    )

    assert result.valid is True
    assert (
        result.status
        == ValidationStatus.REVIEW_REQUIRED
    )

    assert any(
        issue.code == "AI_REVIEW_REQUIRED"
        for issue in result.warnings
    )


def test_low_confidence_and_review_can_coexist():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.50,
            requires_review=True,
        )
    )

    assert (
        result.status
        == ValidationStatus.REVIEW_REQUIRED
    )

    codes = {
        issue.code
        for issue in result.warnings
    }

    assert "LOW_AI_CONFIDENCE" in codes
    assert "AI_REVIEW_REQUIRED" in codes


def test_custom_threshold():
    config = RuleValidationConfig(
        confidence_threshold=0.90
    )

    validator = AccountingRuleValidator(
        config
    )

    result = validator.validate(
        make_transaction(
            confidence=0.85
        )
    )

    assert (
        result.status
        == ValidationStatus.REVIEW_REQUIRED
    )


def test_high_confidence_with_review_is_not_invalid():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.99,
            requires_review=True,
        )
    )

    assert result.valid is True
    assert (
        result.status
        == ValidationStatus.REVIEW_REQUIRED
    )


def test_validate_many():
    validator = AccountingRuleValidator()

    transactions = (
        make_transaction(Decimal("1000")),
        make_transaction(Decimal("2000")),
        make_transaction(Decimal("3000")),
    )

    results = validator.validate_many(
        transactions
    )

    assert len(results) == 3
    assert all(
        result.valid
        for result in results
    )


def test_validate_many_preserves_order():
    validator = AccountingRuleValidator()

    transactions = (
        make_transaction(
            Decimal("1000"),
            confidence=0.95,
        ),
        make_transaction(
            Decimal("2000"),
            confidence=0.60,
        ),
        make_transaction(
            Decimal("3000"),
            confidence=0.99,
        ),
    )

    results = validator.validate_many(
        transactions
    )

    assert results[0].confidence == 0.95
    assert results[1].confidence == 0.60
    assert results[2].confidence == 0.99


def test_service_validate():
    service = RuleValidationService()

    result = service.validate(
        make_transaction()
    )

    assert result.valid is True


def test_service_validate_many():
    service = RuleValidationService()

    results = service.validate_many(
        (
            make_transaction(),
            make_transaction(
                Decimal("2500")
            ),
        )
    )

    assert len(results) == 2
    assert all(
        result.valid
        for result in results
    )


def test_service_ready():
    service = RuleValidationService()

    assert service.is_ready() is True


def test_result_has_no_errors_for_valid_transaction():
    result = AccountingRuleValidator().validate(
        make_transaction()
    )

    assert result.issues == ()


def test_result_has_no_warnings_for_high_confidence_transaction():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.95,
            requires_review=False,
        )
    )

    assert result.warnings == ()


def test_result_is_immutable():
    result = AccountingRuleValidator().validate(
        make_transaction()
    )

    with pytest.raises(
        AttributeError
    ):
        result.valid = False


def test_config_is_immutable():
    config = RuleValidationConfig()

    with pytest.raises(
        AttributeError
    ):
        config.confidence_threshold = 0.50


def test_validation_status_values():
    assert ValidationStatus.VALID.value == "valid"
    assert ValidationStatus.INVALID.value == "invalid"
    assert (
        ValidationStatus.REVIEW_REQUIRED.value
        == "review_required"
    )


def test_validation_severity_values():
    assert (
        ValidationSeverity.ERROR.value
        == "error"
    )

    assert (
        ValidationSeverity.WARNING.value
        == "warning"
    )


def test_multiple_warnings_are_returned():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.50,
            requires_review=True,
        )
    )

    assert len(result.warnings) == 2


def test_valid_result_preserves_ai_confidence():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.87
        )
    )

    assert result.confidence == 0.87


def test_review_result_preserves_ai_confidence():
    result = AccountingRuleValidator().validate(
        make_transaction(
            confidence=0.65
        )
    )

    assert result.confidence == 0.65
