import pytest

from ml.transaction_understanding.confidence.config import (
    ConfidenceConfig,
)
from ml.transaction_understanding.confidence.inference import (
    ConfidenceService,
)
from ml.transaction_understanding.confidence.schemas import (
    ConfidenceScore,
    ConfidenceSignals,
)
from ml.transaction_understanding.confidence.scorer import (
    ConfidenceScorer,
)


def test_default_config():
    config = ConfidenceConfig()

    assert config.classification_weight == 0.25
    assert config.account_weight == 0.25
    assert config.debit_credit_weight == 0.20
    assert config.payment_mode_weight == 0.10
    assert config.semantic_weight == 0.20
    assert config.threshold == 0.80


def test_weights_sum_to_one():
    config = ConfidenceConfig()

    total = (
        config.classification_weight
        + config.account_weight
        + config.debit_credit_weight
        + config.payment_mode_weight
        + config.semantic_weight
    )

    assert total == pytest.approx(1.0)


def test_custom_config():
    config = ConfidenceConfig(
        classification_weight=0.30,
        account_weight=0.20,
        debit_credit_weight=0.20,
        payment_mode_weight=0.10,
        semantic_weight=0.20,
        threshold=0.75,
    )

    assert config.threshold == 0.75


def test_config_rejects_invalid_weight():
    with pytest.raises(ValueError):
        ConfidenceConfig(
            classification_weight=1.5,
            account_weight=0.0,
            debit_credit_weight=0.0,
            payment_mode_weight=0.0,
            semantic_weight=0.0,
        )


def test_config_rejects_negative_weight():
    with pytest.raises(ValueError):
        ConfidenceConfig(
            classification_weight=-0.1,
        )


def test_config_rejects_weights_not_summing_to_one():
    with pytest.raises(ValueError):
        ConfidenceConfig(
            classification_weight=0.50,
            account_weight=0.10,
            debit_credit_weight=0.10,
            payment_mode_weight=0.10,
            semantic_weight=0.10,
        )


def test_config_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        ConfidenceConfig(threshold=1.5)


def test_config_rejects_negative_threshold():
    with pytest.raises(ValueError):
        ConfidenceConfig(threshold=-0.1)


def test_confidence_signals():
    signals = ConfidenceSignals(
        classification=0.90,
        account=0.85,
        debit_credit=0.95,
        payment_mode=0.98,
        semantic=0.88,
    )

    assert signals.classification == 0.90
    assert signals.account == 0.85
    assert signals.debit_credit == 0.95
    assert signals.payment_mode == 0.98
    assert signals.semantic == 0.88


def test_signals_reject_value_above_one():
    with pytest.raises(ValueError):
        ConfidenceSignals(
            classification=1.1,
            account=0.8,
            debit_credit=0.8,
            payment_mode=0.8,
            semantic=0.8,
        )


def test_signals_reject_negative_value():
    with pytest.raises(ValueError):
        ConfidenceSignals(
            classification=-0.1,
            account=0.8,
            debit_credit=0.8,
            payment_mode=0.8,
            semantic=0.8,
        )


def test_all_zero_signals():
    signals = ConfidenceSignals(
        classification=0.0,
        account=0.0,
        debit_credit=0.0,
        payment_mode=0.0,
        semantic=0.0,
    )

    scorer = ConfidenceScorer()

    result = scorer.score(signals)

    assert result.overall == 0.0
    assert result.requires_review is True


def test_all_one_signals():
    signals = ConfidenceSignals(
        classification=1.0,
        account=1.0,
        debit_credit=1.0,
        payment_mode=1.0,
        semantic=1.0,
    )

    scorer = ConfidenceScorer()

    result = scorer.score(signals)

    assert result.overall == pytest.approx(1.0)
    assert result.requires_review is False


def test_weighted_score():
    signals = ConfidenceSignals(
        classification=0.80,
        account=0.90,
        debit_credit=0.70,
        payment_mode=0.60,
        semantic=0.85,
    )

    scorer = ConfidenceScorer()

    result = scorer.score(signals)

    expected = (
        0.80 * 0.25
        + 0.90 * 0.25
        + 0.70 * 0.20
        + 0.60 * 0.10
        + 0.85 * 0.20
    )

    assert result.overall == pytest.approx(expected)


def test_high_confidence_does_not_require_review():
    signals = ConfidenceSignals(
        classification=0.95,
        account=0.95,
        debit_credit=0.95,
        payment_mode=0.95,
        semantic=0.95,
    )

    result = ConfidenceScorer().score(signals)

    assert result.overall >= 0.80
    assert result.requires_review is False
    assert "Automatic processing" in result.reason


def test_low_confidence_requires_review():
    signals = ConfidenceSignals(
        classification=0.40,
        account=0.50,
        debit_credit=0.45,
        payment_mode=0.30,
        semantic=0.40,
    )

    result = ConfidenceScorer().score(signals)

    assert result.overall < 0.80
    assert result.requires_review is True
    assert "Human review" in result.reason


def test_threshold_boundary_allows_processing():
    config = ConfidenceConfig(
        threshold=0.80,
    )

    signals = ConfidenceSignals(
        classification=0.80,
        account=0.80,
        debit_credit=0.80,
        payment_mode=0.80,
        semantic=0.80,
    )

    result = ConfidenceScorer(config).score(signals)

    assert result.overall == pytest.approx(0.80)
    assert result.requires_review is False


def test_threshold_just_below_requires_review():
    config = ConfidenceConfig(
        threshold=0.80,
    )

    signals = ConfidenceSignals(
        classification=0.79,
        account=0.79,
        debit_credit=0.79,
        payment_mode=0.79,
        semantic=0.79,
    )

    result = ConfidenceScorer(config).score(signals)

    assert result.overall == pytest.approx(0.79)
    assert result.requires_review is True


def test_custom_weights_affect_score():
    config = ConfidenceConfig(
        classification_weight=1.0,
        account_weight=0.0,
        debit_credit_weight=0.0,
        payment_mode_weight=0.0,
        semantic_weight=0.0,
    )

    signals = ConfidenceSignals(
        classification=0.73,
        account=0.10,
        debit_credit=0.10,
        payment_mode=0.10,
        semantic=0.10,
    )

    result = ConfidenceScorer(config).score(signals)

    assert result.overall == pytest.approx(0.73)


def test_account_weight_can_dominate():
    config = ConfidenceConfig(
        classification_weight=0.0,
        account_weight=1.0,
        debit_credit_weight=0.0,
        payment_mode_weight=0.0,
        semantic_weight=0.0,
    )

    signals = ConfidenceSignals(
        classification=0.10,
        account=0.91,
        debit_credit=0.10,
        payment_mode=0.10,
        semantic=0.10,
    )

    result = ConfidenceScorer(config).score(signals)

    assert result.overall == pytest.approx(0.91)


def test_score_values():
    scorer = ConfidenceScorer()

    result = scorer.score_values(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.90,
        semantic=0.90,
    )

    assert result.overall == pytest.approx(0.90)


def test_score_preserves_signals():
    signals = ConfidenceSignals(
        classification=0.90,
        account=0.80,
        debit_credit=0.70,
        payment_mode=0.60,
        semantic=0.50,
    )

    result = ConfidenceScorer().score(signals)

    assert result.signals == signals


def test_score_returns_correct_type():
    signals = ConfidenceSignals(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.90,
        semantic=0.90,
    )

    result = ConfidenceScorer().score(signals)

    assert isinstance(result, ConfidenceScore)


def test_scorer_rejects_invalid_signal_type():
    with pytest.raises(TypeError):
        ConfidenceScorer().score("invalid")


def test_reason_contains_score():
    signals = ConfidenceSignals(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.90,
        semantic=0.90,
    )

    result = ConfidenceScorer().score(signals)

    assert "0.900" in result.reason


def test_is_ready():
    assert ConfidenceScorer().is_ready() is True


def test_service_score():
    service = ConfidenceService()

    signals = ConfidenceSignals(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.90,
        semantic=0.90,
    )

    result = service.score(signals)

    assert isinstance(result, ConfidenceScore)


def test_service_score_values():
    service = ConfidenceService()

    result = service.score_values(
        classification=0.85,
        account=0.85,
        debit_credit=0.85,
        payment_mode=0.85,
        semantic=0.85,
    )

    assert result.overall == pytest.approx(0.85)


def test_service_is_ready():
    assert ConfidenceService().is_ready() is True


def test_score_is_bounded():
    signals = ConfidenceSignals(
        classification=1.0,
        account=1.0,
        debit_credit=1.0,
        payment_mode=1.0,
        semantic=1.0,
    )

    result = ConfidenceScorer().score(signals)

    assert 0.0 <= result.overall <= 1.0


def test_review_flag_is_boolean():
    signals = ConfidenceSignals(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.90,
        semantic=0.90,
    )

    result = ConfidenceScorer().score(signals)

    assert isinstance(result.requires_review, bool)


def test_reason_is_non_empty():
    signals = ConfidenceSignals(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.90,
        semantic=0.90,
    )

    result = ConfidenceScorer().score(signals)

    assert result.reason.strip()


def test_semantic_signal_affects_score():
    low = ConfidenceSignals(
        classification=0.9,
        account=0.9,
        debit_credit=0.9,
        payment_mode=0.9,
        semantic=0.0,
    )

    high = ConfidenceSignals(
        classification=0.9,
        account=0.9,
        debit_credit=0.9,
        payment_mode=0.9,
        semantic=1.0,
    )

    scorer = ConfidenceScorer()

    low_result = scorer.score(low)
    high_result = scorer.score(high)

    assert high_result.overall > low_result.overall


def test_classification_signal_affects_score():
    low = ConfidenceSignals(
        classification=0.0,
        account=0.9,
        debit_credit=0.9,
        payment_mode=0.9,
        semantic=0.9,
    )

    high = ConfidenceSignals(
        classification=1.0,
        account=0.9,
        debit_credit=0.9,
        payment_mode=0.9,
        semantic=0.9,
    )

    scorer = ConfidenceScorer()

    assert scorer.score(high).overall > scorer.score(low).overall


def test_debit_credit_signal_affects_score():
    low = ConfidenceSignals(
        classification=0.9,
        account=0.9,
        debit_credit=0.0,
        payment_mode=0.9,
        semantic=0.9,
    )

    high = ConfidenceSignals(
        classification=0.9,
        account=0.9,
        debit_credit=1.0,
        payment_mode=0.9,
        semantic=0.9,
    )

    scorer = ConfidenceScorer()

    assert scorer.score(high).overall > scorer.score(low).overall


def test_payment_mode_signal_affects_score():
    low = ConfidenceSignals(
        classification=0.9,
        account=0.9,
        debit_credit=0.9,
        payment_mode=0.0,
        semantic=0.9,
    )

    high = ConfidenceSignals(
        classification=0.9,
        account=0.9,
        debit_credit=0.9,
        payment_mode=1.0,
        semantic=0.9,
    )

    scorer = ConfidenceScorer()

    assert scorer.score(high).overall > scorer.score(low).overall


def test_account_signal_affects_score():
    low = ConfidenceSignals(
        classification=0.9,
        account=0.0,
        debit_credit=0.9,
        payment_mode=0.9,
        semantic=0.9,
    )

    high = ConfidenceSignals(
        classification=0.9,
        account=1.0,
        debit_credit=0.9,
        payment_mode=0.9,
        semantic=0.9,
    )

    scorer = ConfidenceScorer()

    assert scorer.score(high).overall > scorer.score(low).overall


def test_five_signal_average_with_equal_weights():
    config = ConfidenceConfig(
        classification_weight=0.20,
        account_weight=0.20,
        debit_credit_weight=0.20,
        payment_mode_weight=0.20,
        semantic_weight=0.20,
    )

    signals = ConfidenceSignals(
        classification=0.60,
        account=0.70,
        debit_credit=0.80,
        payment_mode=0.90,
        semantic=1.00,
    )

    result = ConfidenceScorer(config).score(signals)

    assert result.overall == pytest.approx(0.80)
