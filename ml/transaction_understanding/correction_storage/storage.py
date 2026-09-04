from __future__ import annotations

from typing import Iterable

from ..review_decision.schemas import ReviewDecision
from ..review_queue.schemas import ReviewQueueItem
from ..transaction_editing.schemas import TransactionEditResult
from .config import CorrectionStorageConfig
from .schemas import (
    CorrectionRecord,
    CorrectionStatus,
    utc_now,
)


class CorrectionStore:
    """
    In-memory correction repository.

    Persistence can be connected later without changing the
    correction domain contract.
    """

    def __init__(
        self,
        config: CorrectionStorageConfig | None = None,
    ) -> None:
        self.config = config or CorrectionStorageConfig()
        self._records: dict[str, CorrectionRecord] = {}

    def store(
        self,
        edit_result: TransactionEditResult,
        decision_result,
        *,
        metadata: dict | None = None,
        created_at=None,
    ) -> CorrectionRecord:
        if not isinstance(
            edit_result,
            TransactionEditResult,
        ):
            raise TypeError(
                "edit_result must be TransactionEditResult."
            )

        if not hasattr(
            decision_result,
            "transaction_id",
        ):
            raise TypeError(
                "decision_result must be ReviewDecisionResult."
            )

        from ..review_decision.schemas import ReviewDecisionResult

        if not isinstance(
            decision_result,
            ReviewDecisionResult,
        ):
            raise TypeError(
                "decision_result must be ReviewDecisionResult."
            )

        if (
            edit_result.original.transaction_id
            != decision_result.transaction_id
        ):
            raise ValueError(
                "Edit and decision transaction IDs must match."
            )

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

        if len(metadata) > self.config.max_metadata_entries:
            raise ValueError(
                "metadata exceeds the configured maximum number "
                "of entries."
            )

        if len(self._records) >= self.config.max_records:
            raise ValueError(
                "Correction store has reached its maximum capacity."
            )

        correction_id = (
            f"CORRECTION-{decision_result.review_id}"
        )

        if correction_id in self._records:
            raise ValueError(
                "A correction record already exists for this review."
            )

        status = (
            CorrectionStatus.APPROVED
            if decision_result.decision
            == ReviewDecision.APPROVED
            else CorrectionStatus.REJECTED
        )

        timestamp = created_at or utc_now()

        if timestamp.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        record = CorrectionRecord(
            correction_id=correction_id,
            transaction_id=edit_result.original.transaction_id,
            review_id=decision_result.review_id,
            edit_result=edit_result,
            decision_result=decision_result,
            status=status,
            created_at=timestamp,
            metadata=dict(metadata),
        )

        self._records[correction_id] = record

        return record

    def get(
        self,
        correction_id: str,
    ) -> CorrectionRecord:
        if correction_id not in self._records:
            raise KeyError(
                f"Unknown correction ID: {correction_id}"
            )

        return self._records[correction_id]

    def get_by_transaction(
        self,
        transaction_id: str,
    ) -> CorrectionRecord:
        for record in self._records.values():
            if record.transaction_id == transaction_id:
                return record

        raise KeyError(
            f"No correction found for transaction: {transaction_id}"
        )

    def get_by_review(
        self,
        review_id: str,
    ) -> CorrectionRecord:
        for record in self._records.values():
            if record.review_id == review_id:
                return record

        raise KeyError(
            f"No correction found for review: {review_id}"
        )

    def list_all(self) -> tuple[CorrectionRecord, ...]:
        return tuple(
            sorted(
                self._records.values(),
                key=lambda record: record.created_at,
            )
        )

    def list_approved(self) -> tuple[CorrectionRecord, ...]:
        return tuple(
            record
            for record in self.list_all()
            if record.status == CorrectionStatus.APPROVED
        )

    def list_rejected(self) -> tuple[CorrectionRecord, ...]:
        return tuple(
            record
            for record in self.list_all()
            if record.status == CorrectionStatus.REJECTED
        )

    def remove(
        self,
        correction_id: str,
    ) -> CorrectionRecord:
        if correction_id not in self._records:
            raise KeyError(
                f"Unknown correction ID: {correction_id}"
            )

        return self._records.pop(correction_id)

    def contains(
        self,
        correction_id: str,
    ) -> bool:
        return correction_id in self._records

    def __len__(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()

    def is_ready(self) -> bool:
        return True

    def store_many(
        self,
        records: Iterable[
            tuple[
                TransactionEditResult,
                object,
            ]
        ],
    ) -> tuple[CorrectionRecord, ...]:
        results = []

        for edit_result, decision_result in records:
            results.append(
                self.store(
                    edit_result,
                    decision_result,
                )
            )

        return tuple(results)
