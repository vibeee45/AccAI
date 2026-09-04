import pytest

from ml.transaction_understanding.payment_mode import (
    PaymentMode,
    PaymentModeConfig,
    PaymentModeDetector,
    PaymentModeService,
)


def create_detector():
    return PaymentModeDetector(
        PaymentModeConfig(
            confidence_threshold=0.80,
            rule_confidence=0.98,
            fallback_confidence=0.50,
        )
    )


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

def test_config_defaults():
    config = PaymentModeConfig()

    assert config.confidence_threshold == 0.80
    assert config.rule_confidence == 0.98
    assert config.fallback_confidence == 0.50


def test_config_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        PaymentModeConfig(confidence_threshold=1.5)


def test_config_rejects_invalid_rule_confidence():
    with pytest.raises(ValueError):
        PaymentModeConfig(rule_confidence=-0.1)


def test_config_rejects_invalid_fallback_confidence():
    with pytest.raises(ValueError):
        PaymentModeConfig(fallback_confidence=1.5)


# ------------------------------------------------------------------
# Explicit payment modes
# ------------------------------------------------------------------

def test_detect_upi():
    result = create_detector().detect(
        "Paid office rent Rs 25000 through UPI"
    )

    assert result.payment_mode == PaymentMode.UPI
    assert result.confidence == 0.98
    assert result.requires_review is False


def test_detect_neft():
    result = create_detector().detect(
        "Paid supplier through NEFT"
    )

    assert result.payment_mode == PaymentMode.NEFT


def test_detect_rtgs():
    result = create_detector().detect(
        "Transferred payment through RTGS"
    )

    assert result.payment_mode == PaymentMode.RTGS


def test_detect_imps():
    result = create_detector().detect(
        "Paid vendor using IMPS"
    )

    assert result.payment_mode == PaymentMode.IMPS


def test_detect_cheque():
    result = create_detector().detect(
        "Purchased goods by cheque"
    )

    assert result.payment_mode == PaymentMode.CHEQUE


def test_detect_check():
    result = create_detector().detect(
        "Paid supplier by check"
    )

    assert result.payment_mode == PaymentMode.CHEQUE


def test_detect_cash():
    result = create_detector().detect(
        "Paid rent in cash"
    )

    assert result.payment_mode == PaymentMode.CASH


def test_detect_bank_transfer():
    result = create_detector().detect(
        "Transferred amount through bank transfer"
    )

    assert result.payment_mode == PaymentMode.BANK_TRANSFER


def test_detect_debit_card():
    result = create_detector().detect(
        "Paid using debit card"
    )

    assert result.payment_mode == PaymentMode.DEBIT_CARD


def test_detect_credit_card():
    result = create_detector().detect(
        "Paid using credit card"
    )

    assert result.payment_mode == PaymentMode.CREDIT_CARD


def test_detect_generic_card():
    result = create_detector().detect(
        "Payment made by card"
    )

    assert result.payment_mode == PaymentMode.CARD


# ------------------------------------------------------------------
# Alternative UPI names
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Paid through Google Pay",
        "Paid using GPay",
        "Paid through PhonePe",
        "Paid using Paytm",
        "Paid through BHIM",
    ],
)
def test_detect_upi_variations(text):
    result = create_detector().detect(text)

    assert result.payment_mode == PaymentMode.UPI


# ------------------------------------------------------------------
# Case and whitespace handling
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("paid through UPI", PaymentMode.UPI),
        ("PAID THROUGH NEFT", PaymentMode.NEFT),
        ("Paid Through RtGs", PaymentMode.RTGS),
        ("  paid through imps  ", PaymentMode.IMPS),
        ("paid by CHEQUE", PaymentMode.CHEQUE),
        ("paid in CASH", PaymentMode.CASH),
    ],
)
def test_case_and_whitespace_handling(text, expected):
    result = create_detector().detect(text)

    assert result.payment_mode == expected


# ------------------------------------------------------------------
# Unknown / ambiguous transactions
# ------------------------------------------------------------------

def test_unknown_payment_mode_requires_review():
    result = create_detector().detect(
        "Purchased office supplies for Rs 5000"
    )

    assert result.payment_mode == PaymentMode.UNKNOWN
    assert result.confidence == 0.50
    assert result.requires_review is True


def test_unknown_payment_mode_reason_mentions_review():
    result = create_detector().detect(
        "Purchased goods for Rs 10000"
    )

    assert "review" in result.reason.lower()


def test_multiple_payment_modes_require_review():
    result = create_detector().detect(
        "Paid supplier by cash and cheque"
    )

    assert result.payment_mode == PaymentMode.UNKNOWN
    assert result.confidence == 0.50
    assert result.requires_review is True


def test_multiple_payment_modes_reason_mentions_review():
    result = create_detector().detect(
        "Paid using UPI and cash"
    )

    assert "review" in result.reason.lower()


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def test_detector_rejects_empty_text():
    with pytest.raises(ValueError):
        create_detector().detect("")


def test_detector_rejects_whitespace_text():
    with pytest.raises(ValueError):
        create_detector().detect("   ")


def test_detector_rejects_non_string_text():
    with pytest.raises(TypeError):
        create_detector().detect(123)


# ------------------------------------------------------------------
# Confidence
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Paid through UPI",
        "Paid through NEFT",
        "Paid through RTGS",
        "Paid through IMPS",
        "Paid by cheque",
        "Paid in cash",
        "Paid by debit card",
        "Paid by credit card",
    ],
)
def test_known_payment_mode_confidence(text):
    result = create_detector().detect(text)

    assert 0 <= result.confidence <= 1
    assert result.confidence == 0.98


def test_unknown_payment_mode_confidence():
    result = create_detector().detect(
        "Purchased goods"
    )

    assert 0 <= result.confidence <= 1
    assert result.confidence == 0.50


# ------------------------------------------------------------------
# Batch detection
# ------------------------------------------------------------------

def test_detect_many():
    detector = create_detector()

    results = detector.detect_many(
        [
            "Paid rent through UPI",
            "Paid supplier through NEFT",
            "Received cash from customer",
        ]
    )

    assert len(results) == 3
    assert results[0].payment_mode == PaymentMode.UPI
    assert results[1].payment_mode == PaymentMode.NEFT
    assert results[2].payment_mode == PaymentMode.CASH


def test_detect_many_rejects_empty():
    with pytest.raises(ValueError):
        create_detector().detect_many([])


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------

def test_service_is_ready():
    service = PaymentModeService()

    assert service.is_ready() is True


def test_service_detect():
    service = PaymentModeService()

    result = service.detect(
        "Paid supplier through UPI"
    )

    assert result.payment_mode == PaymentMode.UPI
    assert result.confidence == 0.98
    assert result.requires_review is False


def test_service_detect_many():
    service = PaymentModeService()

    results = service.detect_many(
        [
            "Paid rent through UPI",
            "Paid supplier through cheque",
        ]
    )

    assert len(results) == 2
    assert results[0].payment_mode == PaymentMode.UPI
    assert results[1].payment_mode == PaymentMode.CHEQUE


# ------------------------------------------------------------------
# Prediction schema
# ------------------------------------------------------------------

def test_prediction_contains_reason():
    result = create_detector().detect(
        "Paid through UPI"
    )

    assert result.reason
    assert isinstance(result.reason, str)


def test_prediction_confidence_range():
    result = create_detector().detect(
        "Paid through UPI"
    )

    assert 0 <= result.confidence <= 1


def test_prediction_review_flag_is_boolean():
    result = create_detector().detect(
        "Paid through UPI"
    )

    assert isinstance(result.requires_review, bool)
