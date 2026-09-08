from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HistoricalBehaviorConfig:
    minimum_history: int = 1
    max_history: int | None = None

    def __post_init__(self) -> None:
        if self.minimum_history < 0:
            raise ValueError(
                "minimum_history cannot be negative."
            )

        if self.max_history is not None:
            if self.max_history <= 0:
                raise ValueError(
                    "max_history must be positive."
                )

            if self.max_history < self.minimum_history:
                raise ValueError(
                    "max_history cannot be less than minimum_history."
                )
