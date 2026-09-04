from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceSignals:
    classification: float
    account: float
    debit_credit: float
    payment_mode: float
    semantic: float

    def __post_init__(self) -> None:
        values = (
            self.classification,
            self.account,
            self.debit_credit,
            self.payment_mode,
            self.semantic,
        )

        if any(
            not 0.0 <= value <= 1.0
            for value in values
        ):
            raise ValueError(
                "All confidence signals must be between 0 and 1."
            )


@dataclass(frozen=True)
class ConfidenceScore:
    overall: float
    requires_review: bool
    signals: ConfidenceSignals
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall <= 1.0:
            raise ValueError(
                "overall confidence must be between 0 and 1."
            )

        if not isinstance(self.requires_review, bool):
            raise TypeError(
                "requires_review must be a boolean."
            )

        if not isinstance(
            self.signals,
            ConfidenceSignals,
        ):
            raise TypeError(
                "signals must be ConfidenceSignals."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason cannot be empty."
            )
