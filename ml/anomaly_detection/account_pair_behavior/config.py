from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccountPairBehaviorConfig:
    max_history: int | None = None

    def __post_init__(self) -> None:
        if self.max_history is not None and self.max_history <= 0:
            raise ValueError("max_history must be positive.")
