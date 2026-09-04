from __future__ import annotations

import pytest

from ml.transaction_understanding.confidence.schemas import (
    ConfidenceScore,
    ConfidenceSignals,
)
from ml.transaction_understanding.low_confidence.config import (
    LowConfidenceConfig,
)
from ml.transaction_understanding.low_confidence.detector import (
    LowConfidenceDetector,
)
from ml.transaction_understanding.low_confidence.inference import (
    LowConfidenceService,
)
from ml.transaction_understanding.low_confidence.schemas import (
    ConfidenceLevel,
    LowConfidenceDetection,
    LowConfidenceSignal,
)


def make_score(
    classification: float = 0.90,
    account: float = 0.90,
    debit_credit: float = 0.90,
    payment_mode: float = 0.90,
    semantic: float = 0.90,
    overall: float = 0.90,
    requires_review: bool = False,
) -> ConfidenceScore:
    signals = ConfidenceSignals(
        classification=classification,
        account=account,
        debit_credit=debit_credit,
        payment_mode=payment_mode,
        semantic=semantic,
    )

    return ConfidenceScore(
        overall=overall,
        requires_review=requires_review,
        signals=signals,
        reason="test confidence score",
    )


def test_config_defaults():
    config = LowConfidenceConfig()

    assert config.high_threshold == 0.80
    assert config.review_threshold == 0.50
    assert config.weak_signal_threshold == 0.50
    assert config.signal_gap_threshold == 0.20


def test_config_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        LowConfidenceConfig(high_threshold=1.1)

    with pytest.raises(ValueError):
        LowConfidenceConfig(review_threshold=-0.1)


def test_config_rejects_review_above_high():
    with pytest.raises(ValueError):
        LowConfidenceConfig(
            high_threshold=0.60,
            review_threshold=0.70,
        )


def test_signal_valid():
    signal = LowConfidenceSignal(
        name="account",
        value=0.40,
        reason="weak account prediction",
    )

    assert signal.name == "account"
    assert signal.value == 0.40


def test_signal_rejects_empty_name():
    with pytest.raises(ValueError):
        LowConfidenceSignal(
            name="",
            value=0.40,
            reason="weak signal",
        )


def test_signal_rejects_invalid_value():
    with pytest.raises(ValueError):
        LowConfidenceSignal(
            name="account",
            value=1.5,
            reason="invalid",
        )


def test_signal_rejects_empty_reason():
    with pytest.raises(ValueError):
        LowConfidenceSignal(
            name="account",
            value=0.40,
            reason="",
        )


def test_detection_schema():
    detection = LowConfidenceDetection(
        overall=0.45,
        level=ConfidenceLevel.LOW,
        requires_review=True,
        signals=(
            LowConfidenceSignal(
                name="account",
                value=0.30,
                reason="weak account prediction",
            ),
        ),
        reason="review required",
    )

    assert detection.overall == 0.45
    assert detection.level == ConfidenceLevel.LOW
    assert detection.requires_review is True
    assert len(detection.signals) == 1


def test_detection_rejects_invalid_overall():
    with pytest.raises(ValueError):
        LowConfidenceDetection(
            overall=1.5,
            level=ConfidenceLevel.HIGH,
            requires_review=False,
            signals=(),
            reason="invalid",
        )


def test_detection_rejects_invalid_level():
    with pytest.raises(TypeError):
        LowConfidenceDetection(
            overall=0.90,
            level="high",
            requires_review=False,
            signals=(),
            reason="invalid",
        )


def test_detection_rejects_non_tuple_signals():
    with pytest.raises(TypeError):
        LowConfidenceDetection(
            overall=0.90,
            level=ConfidenceLevel.HIGH,
            requires_review=False,
            signals=[],
            reason="invalid",
        )


def test_high_confidence_detection():
    detector = LowConfidenceDetector()

    score = make_score(
        overall=0.95,
    )

    result = detector.detect(score)

    assert result.level == ConfidenceLevel.HIGH
    assert result.requires_review is False
    assert result.overall == 0.95
    assert result.signals == ()
    assert "high-confidence threshold" in result.reason


def test_high_confidence_can_still_report_weak_signal():
    detector = LowConfidenceDetector()

    score = make_score(
        classification=0.95,
        account=0.95,
        debit_credit=0.95,
        payment_mode=0.30,
        semantic=0.95,
        overall=0.82,
    )

    result = detector.detect(score)

    assert result.level == ConfidenceLevel.HIGH
    assert result.requires_review is False
    assert any(
        signal.name == "payment_mode"
        for signal in result.signals
    )


def test_review_required_detection():
    detector = LowConfidenceDetector()

    score = make_score(
        overall=0.65,
        requires_review=True,
    )

    result = detector.detect(score)

    assert result.level == ConfidenceLevel.REVIEW_REQUIRED
    assert result.requires_review is True


def test_low_confidence_detection():
    detector = LowConfidenceDetector()

    score = make_score(
        classification=0.30,
        account=0.40,
        debit_credit=0.45,
        payment_mode=0.40,
        semantic=0.35,
        overall=0.38,
        requires_review=True,
    )

    result = detector.detect(score)

    assert result.level == ConfidenceLevel.LOW
    assert result.requires_review is True
    assert len(result.signals) == 5


def test_weak_signals_are_sorted_by_confidence():
    detector = LowConfidenceDetector()

    score = make_score(
        classification=0.30,
        account=0.45,
        debit_credit=0.20,
        payment_mode=0.40,
        semantic=0.35,
        overall=0.40,
        requires_review=True,
    )

    result = detector.detect(score)

    values = [
        signal.value
        for signal in result.signals
    ]

    assert values == sorted(values)


def test_gap_based_weak_signal_detection():
    detector = LowConfidenceDetector(
        LowConfidenceConfig(
            weak_signal_threshold=0.20,
            signal_gap_threshold=0.20,
        )
    )

    score = make_score(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.60,
        semantic=0.90,
        overall=0.85,
    )

    result = detector.detect(score)

    assert any(
        signal.name == "payment_mode"
        for signal in result.signals
    )


def test_no_false_weak_signal_when_component_is_close():
    detector = LowConfidenceDetector(
        LowConfidenceConfig(
            weak_signal_threshold=0.30,
            signal_gap_threshold=0.20,
        )
    )

    score = make_score(
        classification=0.90,
        account=0.90,
        debit_credit=0.90,
        payment_mode=0.70,
        semantic=0.90,
        overall=0.82,
    )

    result = detector.detect(score)

    assert not any(
        signal.name == "payment_mode"
        for signal in result.signals
    )


def test_detector_rejects_wrong_input():
    detector = LowConfidenceDetector()

    with pytest.raises(TypeError):
        detector.detect("not a confidence score")


def test_detector_is_ready():
    detector = LowConfidenceDetector()

    assert detector.is_ready() is True


def test_service_delegates_to_detector():
    service = LowConfidenceService()

    score = make_score(
        overall=0.40,
        requires_review=True,
    )

    result = service.detect(score)

    assert isinstance(result, LowConfidenceDetection)
    assert result.level == ConfidenceLevel.LOW


def test_service_is_ready():
    service = LowConfidenceService()

    assert service.is_ready() is True


def test_service_rejects_detector_and_config_together():
    detector = LowConfidenceDetector()

    with pytest.raises(ValueError):
        LowConfidenceService(
            detector=detector,
            config=LowConfidenceConfig(),
        )


def test_review_boundary():
    detector = LowConfidenceDetector()

    score = make_score(
        overall=0.50,
        requires_review=True,
    )

    result = detector.detect(score)

    assert result.level == ConfidenceLevel.REVIEW_REQUIRED


def test_high_boundary():
    detector = LowConfidenceDetector()

    score = make_score(
        overall=0.80,
        requires_review=False,
    )

    result = detector.detect(score)

    assert result.level == ConfidenceLevel.HIGH
    assert result.requires_review is False
