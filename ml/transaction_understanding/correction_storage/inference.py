from __future__ import annotations

from datetime import datetime
from typing import Any

from ..review_decision.schemas import ReviewDecisionResult
from ..transaction_editing.schemas import TransactionEditResult
from .config import CorrectionStorageConfig
from .schemas import CorrectionRecord
from .storage import CorrectionStore


class CorrectionStorageService:
    """
    Service layer for correction storage.
    """

    def __init__(
        self,
        store: CorrectionStore | None = None,
        config: CorrectionStorageConfig | None = None,
    ) -> None:
        if store is not None and config is not None:
            raise ValueError(
                "Provide either store or config, not both."
            )

        self.repository = store or CorrectionStore(config)

    def store(
        self,
        edit_result: TransactionEditResult,
        decision_result: ReviewDecisionResult,
        *,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
    ) -> CorrectionRecord:
        return self.repository.store(
            edit_result,
            decision_result,
            metadata=metadata,
            created_at=created_at,
        )

    def get(
        self,
        correction_id: str,
    ) -> CorrectionRecord:
        return self.repository.get(correction_id)

    def get_by_transaction(
        self,
        transaction_id: str,
    ) -> CorrectionRecord:
        return self.repository.get_by_transaction(
            transaction_id
        )

    def get_by_review(
        self,
        review_id: str,
    ) -> CorrectionRecord:
        return self.repository.get_by_review(
            review_id
        )

    def list_all(self) -> tuple[CorrectionRecord, ...]:
        return self.repository.list_all()

    def list_approved(self) -> tuple[CorrectionRecord, ...]:
        return self.repository.list_approved()

    def list_rejected(self) -> tuple[CorrectionRecord, ...]:
        return self.repository.list_rejected()

    def remove(
        self,
        correction_id: str,
    ) -> CorrectionRecord:
        return self.repository.remove(correction_id)

    def contains(
        self,
        correction_id: str,
    ) -> bool:
        return self.repository.contains(correction_id)

    def __len__(self) -> int:
        return len(self.repository)

    def clear(self) -> None:
        self.repository.clear()

    def is_ready(self) -> bool:
        return self.repository.is_ready()
