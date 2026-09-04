from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from ..correction_storage.schemas import (
    CorrectionRecord,
    CorrectionStatus,
)
from .config import FeedbackDatasetConfig
from .schemas import (
    FeedbackDataset,
    FeedbackExample,
    FeedbackLabel,
)


class FeedbackDatasetBuilder:

    def __init__(
        self,
        config: FeedbackDatasetConfig | None = None,
    ) -> None:
        self.config = config or FeedbackDatasetConfig()

    def build_example(
        self,
        correction: CorrectionRecord,
    ) -> FeedbackExample:
        if not isinstance(correction, CorrectionRecord):
            raise TypeError(
                "correction must be a CorrectionRecord"
            )

        edit_result = correction.edit_result
        original = edit_result.original
        corrected = edit_result.edited

        if correction.status == CorrectionStatus.APPROVED:
            label = FeedbackLabel.APPROVED
        elif correction.status == CorrectionStatus.REJECTED:
            label = FeedbackLabel.REJECTED
        else:
            raise ValueError(
                f"Unsupported correction status: {correction.status}"
            )

        return FeedbackExample(
            feedback_id=f"feedback_{uuid4().hex}",
            transaction_id=correction.transaction_id,
            review_id=correction.review_id,

            original_text=original.raw_text,
            corrected_text=corrected.raw_text,

            original_transaction_class=original.transaction_class,
            corrected_transaction_class=corrected.transaction_class,

            original_debit_account_id=original.debit_account_id,
            corrected_debit_account_id=corrected.debit_account_id,

            original_debit_account_name=original.debit_account_name,
            corrected_debit_account_name=corrected.debit_account_name,

            original_credit_account_id=original.credit_account_id,
            corrected_credit_account_id=corrected.credit_account_id,

            original_credit_account_name=original.credit_account_name,
            corrected_credit_account_name=corrected.credit_account_name,

            original_payment_mode=original.payment_mode,
            corrected_payment_mode=corrected.payment_mode,

            original_amount=original.amount,
            corrected_amount=corrected.amount,

            changed_fields=tuple(edit_result.changed_fields),

            label=label,

            reviewer=correction.reviewer,
            reason=correction.decision_reason,

            created_at=correction.created_at,

            metadata={
                **correction.metadata,
                "correction_id": correction.correction_id,
                "decision": correction.status.value,
            },
        )

    def should_include(
        self,
        correction: CorrectionRecord,
    ) -> bool:
        if correction.status == CorrectionStatus.APPROVED:
            if not self.config.include_approved:
                return False

        elif correction.status == CorrectionStatus.REJECTED:
            if not self.config.include_rejected:
                return False

        else:
            return False

        if (
            self.config.require_changes
            and not correction.has_changes
        ):
            return False

        return True

    def build(
        self,
        corrections: Iterable[CorrectionRecord],
    ) -> FeedbackDataset:
        examples: list[FeedbackExample] = []
        seen_keys: set[tuple[str, str]] = set()

        for correction in corrections:
            if not isinstance(correction, CorrectionRecord):
                raise TypeError(
                    "all corrections must be CorrectionRecord objects"
                )

            if not self.should_include(correction):
                continue

            key = (
                correction.transaction_id,
                correction.review_id,
            )

            if self.config.deduplicate:
                if key in seen_keys:
                    continue
                seen_keys.add(key)

            examples.append(
                self.build_example(correction)
            )

            if (
                self.config.max_examples is not None
                and len(examples) >= self.config.max_examples
            ):
                break

        return FeedbackDataset(
            examples=tuple(examples),
            created_at=datetime.now(timezone.utc),
            metadata={
                "source": "correction_storage",
                "include_approved": self.config.include_approved,
                "include_rejected": self.config.include_rejected,
                "require_changes": self.config.require_changes,
                "deduplicate": self.config.deduplicate,
            },
        )
