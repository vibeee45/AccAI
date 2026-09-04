from __future__ import annotations

from datetime import datetime
from typing import Any

from ..prediction.schemas import TransactionPrediction
from .config import TransactionEditingConfig
from .editor import TransactionEditor
from .schemas import TransactionEditResult


class TransactionEditingService:
    """
    Service layer for human transaction editing.
    """

    def __init__(
        self,
        editor: TransactionEditor | None = None,
        config: TransactionEditingConfig | None = None,
    ) -> None:
        if editor is not None and config is not None:
            raise ValueError(
                "Provide either editor or config, not both."
            )

        self.editor = editor or TransactionEditor(config)

    def edit(
        self,
        prediction: TransactionPrediction,
        changes: dict[str, Any],
        *,
        edited_by: str | None = None,
        reason: str = "Human reviewer edited transaction.",
        metadata: dict[str, Any] | None = None,
        edited_at: datetime | None = None,
    ) -> TransactionEditResult:
        return self.editor.edit(
            prediction,
            changes,
            edited_by=edited_by,
            reason=reason,
            metadata=metadata,
            edited_at=edited_at,
        )

    def is_ready(self) -> bool:
        return self.editor.is_ready()
