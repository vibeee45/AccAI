from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewQueueConfig:
    max_queue_size: int = 10000
    default_priority: int = 0

    def __post_init__(self) -> None:
        if self.max_queue_size <= 0:
            raise ValueError(
                "max_queue_size must be greater than zero."
            )

        if self.default_priority < 0:
            raise ValueError(
                "default_priority cannot be negative."
            )
