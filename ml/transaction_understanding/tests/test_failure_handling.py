import pytest

from ml.transaction_understanding.failure_handling import (
    FailureAction,
    FailureDetail,
    FailureHandler,
    FailureHandlingConfig,
    FailureHandlingResult,
    FailureHandlingService,
    FailureType,
)


def test_config_defaults():
    config = FailureHandlingConfig()

    assert config.capture_exception_details is True
    assert config.preserve_metadata is True
    assert config.max_error_message_length == 500


def test_config_custom_values():
    config = FailureHandlingConfig(
        capture_exception_details=False,
        preserve_metadata=False,
        max_error_message_length=100,
    )

    assert config.capture_exception_details is False
    assert config.preserve_metadata is False
    assert config.max_error_message_length == 100


def test_config_rejects_invalid_boolean():
    with pytest.raises(TypeError):
        FailureHandlingConfig(
            capture_exception_details="yes"
        )


def test_config_rejects_invalid_length_type():
    with pytest.raises(TypeError):
        FailureHandlingConfig(
            max_error_message_length="500"
        )


def test_config_rejects_non_positive_length():
    with pytest.raises(ValueError):
        FailureHandlingConfig(
            max_error_message_length=0
        )


def test_failure_detail_success():
    detail = FailureDetail(
        code="TEST_ERROR",
        message="test error",
        failure_type=FailureType.PROCESSING,
        action=FailureAction.RETRY,
    )

    assert detail.code == "TEST_ERROR"
    assert detail.message == "test error"
    assert (
        detail.failure_type
        == FailureType.PROCESSING
    )
    assert (
        detail.action
        == FailureAction.RETRY
    )


def test_failure_detail_rejects_empty_code():
    with pytest.raises(ValueError):
        FailureDetail(
            code="",
            message="error",
            failure_type=FailureType.PROCESSING,
            action=FailureAction.RETRY,
        )


def test_failure_detail_rejects_empty_message():
    with pytest.raises(ValueError):
        FailureDetail(
            code="ERROR",
            message="",
            failure_type=FailureType.PROCESSING,
            action=FailureAction.RETRY,
        )


def test_result_success():
    result = FailureHandlingResult(
        success=True,
        requires_review=False,
        retryable=False,
    )

    assert result.success is True
    assert result.failure is None
    assert result.errors == ()


def test_success_result_cannot_have_failure():
    failure = FailureDetail(
        code="ERROR",
        message="error",
        failure_type=FailureType.PROCESSING,
        action=FailureAction.RETRY,
    )

    with pytest.raises(ValueError):
        FailureHandlingResult(
            success=True,
            requires_review=False,
            retryable=False,
            failure=failure,
        )


def test_failed_result_requires_failure():
    with pytest.raises(ValueError):
        FailureHandlingResult(
            success=False,
            requires_review=True,
            retryable=False,
        )


def test_success_result_cannot_require_review():
    with pytest.raises(ValueError):
        FailureHandlingResult(
            success=True,
            requires_review=True,
            retryable=False,
        )


def test_success_result_cannot_be_retryable():
    with pytest.raises(ValueError):
        FailureHandlingResult(
            success=True,
            requires_review=False,
            retryable=True,
        )


def test_handle_value_error():
    handler = FailureHandler()

    result = handler.handle_exception(
        ValueError("invalid accounting value")
    )

    assert result.success is False
    assert result.requires_review is True
    assert result.retryable is False
    assert result.failure is not None
    assert (
        result.failure.failure_type
        == FailureType.VALUE_ERROR
    )
    assert (
        result.failure.action
        == FailureAction.REVIEW
    )
    assert (
        result.failure.code
        == "VALUE_ERROR"
    )


def test_handle_type_error():
    handler = FailureHandler()

    result = handler.handle_exception(
        TypeError("invalid type")
    )

    assert result.success is False
    assert result.requires_review is False
    assert result.retryable is False
    assert result.failure.failure_type == (
        FailureType.TYPE_ERROR
    )
    assert result.failure.action == (
        FailureAction.REJECT
    )


def test_handle_processing_error():
    handler = FailureHandler()

    result = handler.handle_exception(
        RuntimeError("temporary processing failure")
    )

    assert result.success is False
    assert result.requires_review is False
    assert result.retryable is True
    assert result.failure.failure_type == (
        FailureType.PROCESSING
    )
    assert result.failure.action == (
        FailureAction.RETRY
    )


def test_handle_exception_requires_exception():
    with pytest.raises(TypeError):
        FailureHandler().handle_exception(
            "not an exception"
        )


def test_validation_failure():
    handler = FailureHandler()

    result = handler.handle_validation_failure(
        [
            "Invalid debit account",
            "Invalid credit account",
        ]
    )

    assert result.success is False
    assert result.requires_review is True
    assert result.retryable is False
    assert result.failure is not None
    assert (
        result.failure.code
        == "VALIDATION_FAILED"
    )
    assert (
        result.failure.failure_type
        == FailureType.VALIDATION
    )
    assert (
        result.failure.action
        == FailureAction.REVIEW
    )
    assert len(result.errors) == 2


def test_validation_failure_accepts_tuple():
    result = FailureHandler().handle_validation_failure(
        (
            "Account mismatch",
            "Low confidence",
        )
    )

    assert result.success is False
    assert len(result.errors) == 2


def test_validation_failure_rejects_invalid_input():
    with pytest.raises(TypeError):
        FailureHandler().handle_validation_failure(
            "single string"
        )


def test_validation_failure_requires_error():
    with pytest.raises(ValueError):
        FailureHandler().handle_validation_failure(
            []
        )


def test_success_handler():
    result = FailureHandler().handle_success()

    assert result.success is True
    assert result.failure is None
    assert result.requires_review is False
    assert result.retryable is False
    assert result.errors == ()


def test_success_preserves_metadata():
    result = FailureHandler().handle_success(
        metadata={
            "transaction_id": "txn-001",
            "source": "excel",
        }
    )

    assert (
        result.metadata["transaction_id"]
        == "txn-001"
    )
    assert result.metadata["source"] == "excel"


def test_exception_preserves_metadata():
    result = FailureHandler().handle_exception(
        ValueError("invalid"),
        metadata={
            "transaction_id": "txn-001"
        },
    )

    assert (
        result.metadata["transaction_id"]
        == "txn-001"
    )


def test_metadata_can_be_disabled():
    handler = FailureHandler(
        FailureHandlingConfig(
            preserve_metadata=False
        )
    )

    result = handler.handle_success(
        metadata={
            "transaction_id": "txn-001"
        }
    )

    assert result.metadata == {}


def test_exception_details_can_be_disabled():
    handler = FailureHandler(
        FailureHandlingConfig(
            capture_exception_details=False
        )
    )

    result = handler.handle_exception(
        ValueError("secret internal message")
    )

    assert (
        result.failure.message
        == "Processing failed."
    )


def test_error_message_is_truncated():
    handler = FailureHandler(
        FailureHandlingConfig(
            max_error_message_length=10
        )
    )

    result = handler.handle_exception(
        ValueError(
            "this is a very long error message"
        )
    )

    assert len(
        result.failure.message
    ) == 10


def test_handle_successful_operation():
    handler = FailureHandler()

    def operation():
        return "success"

    result = handler.handle(
        operation
    )

    assert result.success is True
    assert result.failure is None


def test_handle_failed_operation():
    handler = FailureHandler()

    def operation():
        raise ValueError(
            "accounting validation failed"
        )

    result = handler.handle(
        operation
    )

    assert result.success is False
    assert result.requires_review is True
    assert result.failure is not None


def test_handle_retryable_operation():
    handler = FailureHandler()

    def operation():
        raise RuntimeError(
            "temporary database failure"
        )

    result = handler.handle(
        operation
    )

    assert result.success is False
    assert result.retryable is True


def test_handle_requires_callable():
    with pytest.raises(TypeError):
        FailureHandler().handle(
            "not callable"
        )


def test_service_exception():
    service = FailureHandlingService()

    result = service.handle_exception(
        ValueError("bad transaction")
    )

    assert result.success is False
    assert result.requires_review is True


def test_service_validation_failure():
    service = FailureHandlingService()

    result = service.handle_validation_failure(
        ["Invalid account mapping"]
    )

    assert result.success is False
    assert result.requires_review is True


def test_service_success():
    service = FailureHandlingService()

    result = service.handle_success()

    assert result.success is True


def test_service_handle():
    service = FailureHandlingService()

    result = service.handle(
        lambda: None
    )

    assert result.success is True


def test_service_ready():
    service = FailureHandlingService()

    assert service.is_ready() is True


def test_failure_types():
    assert FailureType.VALIDATION.value == "validation"
    assert FailureType.TYPE_ERROR.value == "type_error"
    assert FailureType.VALUE_ERROR.value == "value_error"
    assert FailureType.PROCESSING.value == "processing"
    assert FailureType.UNKNOWN.value == "unknown"


def test_failure_actions():
    assert FailureAction.RETRY.value == "retry"
    assert FailureAction.REVIEW.value == "review"
    assert FailureAction.REJECT.value == "reject"


def test_failure_result_is_immutable():
    result = FailureHandler().handle_success()

    with pytest.raises(AttributeError):
        result.success = False


def test_failure_detail_is_immutable():
    detail = FailureDetail(
        code="ERROR",
        message="error",
        failure_type=FailureType.PROCESSING,
        action=FailureAction.RETRY,
    )

    with pytest.raises(AttributeError):
        detail.code = "OTHER"


def test_validation_errors_are_cleaned():
    result = FailureHandler().handle_validation_failure(
        [
            "  first error  ",
            "",
            "second error",
            "   ",
        ]
    )

    assert result.errors == (
        "first error",
        "second error",
    )


def test_failure_message_combines_validation_errors():
    result = FailureHandler().handle_validation_failure(
        [
            "Invalid debit",
            "Invalid credit",
        ]
    )

    assert (
        "Invalid debit; Invalid credit"
        == result.failure.message
    )


def test_failure_metadata_is_copied():
    metadata = {
        "source": "excel"
    }

    result = FailureHandler().handle_success(
        metadata=metadata
    )

    metadata["source"] = "changed"

    assert (
        result.metadata["source"]
        == "excel"
    )


def test_service_ready_after_configuration():
    service = FailureHandlingService(
        FailureHandlingConfig(
            max_error_message_length=100
        )
    )

    assert service.is_ready() is True
