from __future__ import annotations

from .config import ConfidenceConfig
from .schemas import ConfidenceScore, ConfidenceSignals
from .scorer import ConfidenceScorer


class ConfidenceService:
    def __init__(
        self,
        config: ConfidenceConfig | None = None,
    ) -> None:
        self.scorer = ConfidenceScorer(config)

    def score(
        self,
        signals: ConfidenceSignals,
    ) -> ConfidenceScore:
        return self.scorer.score(signals)

    def score_values(
        self,
        classification: float,
        account: float,
        debit_credit: float,
        payment_mode: float,
        semantic: float,
    ) -> ConfidenceScore:
        return self.scorer.score_values(
            classification=classification,
            account=account,
            debit_credit=debit_credit,
            payment_mode=payment_mode,
            semantic=semantic,
        )

    def is_ready(self) -> bool:
        return self.scorer.is_ready()
