import pytest

from ml.transaction_understanding.confidence_routing import (
    ConfidenceRouter,
    ConfidenceRoutingConfig,
    ConfidenceRoutingService,
    RoutingDecision,
    RoutingResult,
)


def test_config_defaults():
    config = ConfidenceRoutingConfig()

    assert config.auto_process_threshold == 0.80
    assert config.review_threshold == 0.50


def test_config_custom_values():
    config = ConfidenceRoutingConfig(
        auto_process_threshold=0.90,
        review_threshold=0.60,
    )

    assert config.auto_process_threshold == 0.90
    assert config.review_threshold == 0.60


def test_config_rejects_invalid_auto_threshold():
    with pytest.raises(ValueError):
        ConfidenceRoutingConfig(
            auto_process_threshold=1.5
        )


def test_config_rejects_invalid_review_threshold():
    with pytest.raises(ValueError):
        ConfidenceRoutingConfig(
            review_threshold=-0.1
        )


def test_config_rejects_reversed_thresholds():
    with pytest.raises(ValueError):
        ConfidenceRoutingConfig(
            auto_process_threshold=0.60,
            review_threshold=0.80,
        )


def test_high_confidence_auto_processes():
    result = ConfidenceRouter().route(
        0.95
    )

    assert (
        result.decision
        == RoutingDecision.AUTO_PROCESS
    )

    assert result.requires_review is False
    assert result.retryable is False


def test_exact_auto_threshold_auto_processes():
    result = ConfidenceRouter().route(
        0.80
    )

    assert (
        result.decision
        == RoutingDecision.AUTO_PROCESS
    )


def test_medium_confidence_requires_review():
    result = ConfidenceRouter().route(
        0.65
    )

    assert (
        result.decision
        == RoutingDecision.HUMAN_REVIEW
    )

    assert result.requires_review is True
    assert result.retryable is False


def test_exact_review_threshold_requires_review():
    result = ConfidenceRouter().route(
        0.50
    )

    assert (
        result.decision
        == RoutingDecision.HUMAN_REVIEW
    )


def test_low_confidence_is_rejected():
    result = ConfidenceRouter().route(
        0.20
    )

    assert (
        result.decision
        == RoutingDecision.REJECT
    )

    assert result.requires_review is True
    assert result.retryable is False


def test_zero_confidence_is_rejected():
    result = ConfidenceRouter().route(
        0.0
    )

    assert (
        result.decision
        == RoutingDecision.REJECT
    )


def test_one_confidence_auto_processes():
    result = ConfidenceRouter().route(
        1.0
    )

    assert (
        result.decision
        == RoutingDecision.AUTO_PROCESS
    )


def test_explicit_review_overrides_high_confidence():
    result = ConfidenceRouter().route(
        0.99,
        requires_review=True,
    )

    assert (
        result.decision
        == RoutingDecision.HUMAN_REVIEW
    )

    assert result.requires_review is True


def test_failure_rejects_high_confidence_transaction():
    result = ConfidenceRouter().route(
        0.99,
        failed=True,
    )

    assert (
        result.decision
        == RoutingDecision.REJECT
    )

    assert result.requires_review is True


def test_retryable_failure_is_retryable():
    result = ConfidenceRouter().route(
        0.90,
        failed=True,
        retryable=True,
    )

    assert (
        result.decision
        == RoutingDecision.REJECT
    )

    assert result.retryable is True


def test_failed_transaction_cannot_auto_process():
    result = ConfidenceRouter().route(
        1.0,
        failed=True,
    )

    assert (
        result.decision
        != RoutingDecision.AUTO_PROCESS
    )


def test_confidence_is_preserved():
    result = ConfidenceRouter().route(
        0.73
    )

    assert result.confidence == 0.73


def test_reason_is_present():
    result = ConfidenceRouter().route(
        0.95
    )

    assert result.reason.strip()


def test_metadata_is_preserved():
    result = ConfidenceRouter().route(
        0.95,
        metadata={
            "transaction_id": "txn-001",
            "source": "excel",
        },
    )

    assert (
        result.metadata["transaction_id"]
        == "txn-001"
    )

    assert result.metadata["source"] == "excel"


def test_metadata_is_copied():
    metadata = {
        "source": "excel"
    }

    result = ConfidenceRouter().route(
        0.95,
        metadata=metadata,
    )

    metadata["source"] = "changed"

    assert (
        result.metadata["source"]
        == "excel"
    )


def test_invalid_confidence_type():
    with pytest.raises(TypeError):
        ConfidenceRouter().route(
            "0.95"
        )


def test_boolean_confidence_is_invalid():
    with pytest.raises(TypeError):
        ConfidenceRouter().route(
            True
        )


def test_confidence_above_one_is_invalid():
    with pytest.raises(ValueError):
        ConfidenceRouter().route(
            1.1
        )


def test_confidence_below_zero_is_invalid():
    with pytest.raises(ValueError):
        ConfidenceRouter().route(
            -0.1
        )


def test_requires_review_type_is_validated():
    with pytest.raises(TypeError):
        ConfidenceRouter().route(
            0.90,
            requires_review="yes",
        )


def test_failed_type_is_validated():
    with pytest.raises(TypeError):
        ConfidenceRouter().route(
            0.90,
            failed="yes",
        )


def test_retryable_type_is_validated():
    with pytest.raises(TypeError):
        ConfidenceRouter().route(
            0.90,
            retryable="yes",
        )


def test_route_many():
    router = ConfidenceRouter()

    results = router.route_many(
        (
            0.95,
            0.70,
            0.20,
        )
    )

    assert len(results) == 3

    assert (
        results[0].decision
        == RoutingDecision.AUTO_PROCESS
    )

    assert (
        results[1].decision
        == RoutingDecision.HUMAN_REVIEW
    )

    assert (
        results[2].decision
        == RoutingDecision.REJECT
    )


def test_route_many_preserves_order():
    router = ConfidenceRouter()

    results = router.route_many(
        (
            0.20,
            0.95,
            0.60,
        )
    )

    assert (
        results[0].confidence
        == 0.20
    )

    assert (
        results[1].confidence
        == 0.95
    )

    assert (
        results[2].confidence
        == 0.60
    )


def test_route_many_empty():
    result = ConfidenceRouter().route_many(
        ()
    )

    assert result == ()


def test_service_route():
    service = ConfidenceRoutingService()

    result = service.route(
        0.95
    )

    assert (
        result.decision
        == RoutingDecision.AUTO_PROCESS
    )


def test_service_route_many():
    service = ConfidenceRoutingService()

    results = service.route_many(
        (
            0.95,
            0.60,
        )
    )

    assert len(results) == 2


def test_service_ready():
    service = ConfidenceRoutingService()

    assert service.is_ready() is True


def test_custom_thresholds_are_used():
    router = ConfidenceRouter(
        ConfidenceRoutingConfig(
            auto_process_threshold=0.90,
            review_threshold=0.70,
        )
    )

    result = router.route(
        0.85
    )

    assert (
        result.decision
        == RoutingDecision.HUMAN_REVIEW
    )


def test_custom_threshold_low_confidence():
    router = ConfidenceRouter(
        ConfidenceRoutingConfig(
            auto_process_threshold=0.90,
            review_threshold=0.70,
        )
    )

    result = router.route(
        0.60
    )

    assert (
        result.decision
        == RoutingDecision.REJECT
    )


def test_custom_threshold_high_confidence():
    router = ConfidenceRouter(
        ConfidenceRoutingConfig(
            auto_process_threshold=0.90,
            review_threshold=0.70,
        )
    )

    result = router.route(
        0.95
    )

    assert (
        result.decision
        == RoutingDecision.AUTO_PROCESS
    )


def test_routing_result_confidence_range():
    with pytest.raises(ValueError):
        RoutingResult(
            decision=RoutingDecision.AUTO_PROCESS,
            confidence=2.0,
            reason="test",
            requires_review=False,
        )


def test_routing_result_requires_reason():
    with pytest.raises(ValueError):
        RoutingResult(
            decision=RoutingDecision.AUTO_PROCESS,
            confidence=0.90,
            reason="",
            requires_review=False,
        )


def test_auto_process_cannot_require_review():
    with pytest.raises(ValueError):
        RoutingResult(
            decision=RoutingDecision.AUTO_PROCESS,
            confidence=0.90,
            reason="test",
            requires_review=True,
        )


def test_auto_process_cannot_be_retryable():
    with pytest.raises(ValueError):
        RoutingResult(
            decision=RoutingDecision.AUTO_PROCESS,
            confidence=0.90,
            reason="test",
            requires_review=False,
            retryable=True,
        )


def test_human_review_requires_review_flag():
    with pytest.raises(ValueError):
        RoutingResult(
            decision=RoutingDecision.HUMAN_REVIEW,
            confidence=0.60,
            reason="test",
            requires_review=False,
        )


def test_routing_result_metadata_must_be_dict():
    with pytest.raises(TypeError):
        RoutingResult(
            decision=RoutingDecision.AUTO_PROCESS,
            confidence=0.90,
            reason="test",
            requires_review=False,
            metadata="invalid",
        )


def test_routing_decision_values():
    assert (
        RoutingDecision.AUTO_PROCESS.value
        == "auto_process"
    )

    assert (
        RoutingDecision.HUMAN_REVIEW.value
        == "human_review"
    )

    assert (
        RoutingDecision.REJECT.value
        == "reject"
    )


def test_high_confidence_reason_mentions_threshold():
    result = ConfidenceRouter().route(
        0.95
    )

    assert (
        "threshold"
        in result.reason.lower()
    )


def test_medium_confidence_reason_mentions_review():
    result = ConfidenceRouter().route(
        0.65
    )

    assert (
        "review"
        in result.reason.lower()
    )


def test_low_confidence_reason_mentions_low():
    result = ConfidenceRouter().route(
        0.20
    )

    assert (
        "low"
        in result.reason.lower()
    )


def test_explicit_review_reason():
    result = ConfidenceRouter().route(
        0.99,
        requires_review=True,
    )

    assert (
        "review"
        in result.reason.lower()
    )


def test_failure_reason_mentions_failed():
    result = ConfidenceRouter().route(
        0.99,
        failed=True,
    )

    assert (
        "failed"
        in result.reason.lower()
    )


def test_result_is_immutable():
    result = ConfidenceRouter().route(
        0.95
    )

    with pytest.raises(AttributeError):
        result.confidence = 0.50


def test_config_is_immutable():
    config = ConfidenceRoutingConfig()

    with pytest.raises(AttributeError):
        config.auto_process_threshold = 0.50
