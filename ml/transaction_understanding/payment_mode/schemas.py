from dataclasses import dataclass
from enum import Enum


class PaymentMode(str, Enum):
    CASH = "cash"
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"
    CHEQUE = "cheque"
    BANK_TRANSFER = "bank_transfer"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    CARD = "card"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PaymentModePrediction:
    payment_mode: PaymentMode
    confidence: float
    requires_review: bool
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.payment_mode, PaymentMode):
            raise TypeError(
                "payment_mode must be a PaymentMode."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(self.requires_review, bool):
            raise TypeError(
                "requires_review must be a boolean."
            )

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )
