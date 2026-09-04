from __future__ import annotations

import re

from .schemas import PaymentMode


PAYMENT_MODE_PATTERNS: dict[PaymentMode, tuple[str, ...]] = {
    PaymentMode.UPI: (
        r"\bupi\b",
        r"\bgoogle\s*pay\b",
        r"\bgpay\b",
        r"\bphone\s*pe\b",
        r"\bpaytm\b",
        r"\bbhim\b",
    ),
    PaymentMode.NEFT: (
        r"\bneft\b",
    ),
    PaymentMode.RTGS: (
        r"\brtgs\b",
    ),
    PaymentMode.IMPS: (
        r"\bimps\b",
    ),
    PaymentMode.CHEQUE: (
        r"\bcheque\b",
        r"\bcheck\b",
        r"\bcheq\b",
    ),
    PaymentMode.BANK_TRANSFER: (
        r"\bbank\s+transfer\b",
        r"\btransferred\s+to\s+bank\b",
        r"\bbank\s+transfer(?:red)?\b",
    ),
    PaymentMode.DEBIT_CARD: (
        r"\bdebit\s+card\b",
        r"\bdebit\s+card\s+payment\b",
    ),
    PaymentMode.CREDIT_CARD: (
        r"\bcredit\s+card\b",
        r"\bcredit\s+card\s+payment\b",
    ),
    PaymentMode.CASH: (
        r"\bcash\b",
        r"\bcash\s+payment\b",
        r"\bpaid\s+in\s+cash\b",
        r"\breceived\s+in\s+cash\b",
    ),
    PaymentMode.CARD: (
        r"\bcard\b",
        r"\bcard\s+payment\b",
    ),
}


def normalize_payment_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    text = text.strip().lower()

    text = re.sub(r"\s+", " ", text)

    return text


def detect_payment_modes(
    text: str,
) -> list[PaymentMode]:
    """
    Return all payment modes explicitly detected in the text.

    More specific payment modes such as debit card and credit card
    take precedence over the generic card mode.
    """

    normalized = normalize_payment_text(text)

    matches: list[PaymentMode] = []

    # Detect specific card types first.
    debit_card_detected = any(
        re.search(pattern, normalized)
        for pattern in PAYMENT_MODE_PATTERNS[PaymentMode.DEBIT_CARD]
    )

    credit_card_detected = any(
        re.search(pattern, normalized)
        for pattern in PAYMENT_MODE_PATTERNS[PaymentMode.CREDIT_CARD]
    )

    for mode, patterns in PAYMENT_MODE_PATTERNS.items():

        # Generic CARD must not also match debit card / credit card.
        if mode == PaymentMode.CARD:
            if debit_card_detected or credit_card_detected:
                continue

        for pattern in patterns:
            if re.search(pattern, normalized):
                matches.append(mode)
                break

    return matches
