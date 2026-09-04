from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..review_decision.schemas import (
    ReviewDecision,
    ReviewDecisionResult,
)
from ..transaction_editing.schemas import (
    TransactionEditResult,
)


class CorrectionStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class CorrectionRecord:
    """
    Immutable record combining:

    - original AI-derived transaction values
    - human-edited transaction values
    - human approval/rejection decision
    - reviewer identity
    - reason
    - timestamps
    - metadata

    This record becomes the primary source for Phase 6.6
    feedback-dataset generation.
    """

    correction_id: str
    transaction_id: str
    review_id: str

    edit_result: TransactionEditResult
    decision_result: ReviewDecisionResult

    status: CorrectionStatus

    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.correction_id, str):
            raise TypeError(
                "correction_id must be a string."
            )

        if not self.correction_id.strip():
            raise ValueError(
                "correction_id cannot be empty."
            )

        if not isinstance(self.transaction_id, str):
            raise TypeError(
                "transaction_id must be a string."
            )

        if not self.transaction_id.strip():
            raise ValueError(
                "transaction_id cannot be empty."
            )

        if not isinstance(self.review_id, str):
            raise TypeError(
                "review_id must be a string."
            )

        if not self.review_id.strip():
            raise ValueError(
                "review_id cannot be empty."
            )

        if not isinstance(
            self.edit_result,
            TransactionEditResult,
        ):
            raise TypeError(
                "edit_result must be TransactionEditResult."
            )

        if not isinstance(
            self.decision_result,
            ReviewDecisionResult,
        ):
            raise TypeError(
                "decision_result must be ReviewDecisionResult."
            )

        if not isinstance(
            self.status,
            CorrectionStatus,
        ):
            raise TypeError(
                "status must be CorrectionStatus."
            )

        if (
            self.edit_result.original.transaction_id
            != self.transaction_id
        ):
            raise ValueError(
                "edit result transaction ID does not match record."
            )

        if (
            self.edit_result.edited.transaction_id
            != self.transaction_id
        ):
            raise ValueError(
                "edited transaction ID does not match record."
            )

        if (
            self.decision_result.transaction_id
            != self.transaction_id
        ):
            raise ValueError(
                "decision transaction ID does not match record."
            )

        if (
            self.decision_result.review_id
            != self.review_id
        ):
            raise ValueError(
                "decision review ID does not match record."
            )

        expected_status = (
            CorrectionStatus.APPROVED
            if self.decision_result.decision
            == ReviewDecision.APPROVED
            else CorrectionStatus.REJECTED
        )

        if self.status != expected_status:
            raise ValueError(
                "status does not match decision result."
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be datetime."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

    @property
    def changed_fields(self) -> tuple[str, ...]:
        return self.edit_result.changed_fields

    @property
    def has_changes(self) -> bool:
        return self.edit_result.has_changes

    @property
    def reviewer(self) -> str | None:
        return self.decision_result.decided_by

    @property
    def decision_reason(self) -> str:
        return self.decision_result.reason

    @property
    def original_transaction(self):
        return self.edit_result.original

    @property
    def corrected_transaction(self):
        return self.edit_result.edited


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
