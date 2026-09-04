from __future__ import annotations

from .config import ConfidenceConfig
from .schemas import ConfidenceScore, ConfidenceSignals


class ConfidenceScorer:
    def __init__(
        self,
        config: ConfidenceConfig | None = None,
    ) -> None:
        self.config = config or ConfidenceConfig()

    def score(
        self,
        signals: ConfidenceSignals,
    ) -> ConfidenceScore:
        if not isinstance(
            signals,
            ConfidenceSignals,
        ):
            raise TypeError(
                "signals must be ConfidenceSignals."
            )

        overall = (
            signals.classification
            * self.config.classification_weight
            + signals.account
            * self.config.account_weight
            + signals.debit_credit
            * self.config.debit_credit_weight
            + signals.payment_mode
            * self.config.payment_mode_weight
            + signals.semantic
            * self.config.semantic_weight
        )

        overall = max(
            0.0,
            min(1.0, float(overall)),
        )

        requires_review = (
            overall < self.config.threshold
        )

        if requires_review:
            reason = (
                f"Overall confidence is {overall:.3f}, "
                f"below the review threshold of "
                f"{self.config.threshold:.3f}. "
                "Human review is required."
            )
        else:
            reason = (
                f"Overall confidence is {overall:.3f}, "
                f"meeting the review threshold of "
                f"{self.config.threshold:.3f}. "
                "Automatic processing is allowed."
            )

        return ConfidenceScore(
            overall=overall,
            requires_review=requires_review,
            signals=signals,
            reason=reason,
        )

    def score_values(
        self,
        classification: float,
        account: float,
        debit_credit: float,
        payment_mode: float,
        semantic: float,
    ) -> ConfidenceScore:
        signals = ConfidenceSignals(
            classification=classification,
            account=account,
            debit_credit=debit_credit,
            payment_mode=payment_mode,
            semantic=semantic,
        )

        return self.score(signals)

    def is_ready(self) -> bool:
        return True
