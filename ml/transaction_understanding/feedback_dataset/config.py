from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackDatasetConfig:
    include_approved: bool = True
    include_rejected: bool = False
    require_changes: bool = False
    deduplicate: bool = True
    max_examples: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.include_approved, bool):
            raise TypeError("include_approved must be a bool")
        if not isinstance(self.include_rejected, bool):
            raise TypeError("include_rejected must be a bool")
        if not isinstance(self.require_changes, bool):
            raise TypeError("require_changes must be a bool")
        if not isinstance(self.deduplicate, bool):
            raise TypeError("deduplicate must be a bool")
        if self.max_examples is not None:
            if not isinstance(self.max_examples, int):
                raise TypeError("max_examples must be an int or None")
            if self.max_examples <= 0:
                raise ValueError("max_examples must be greater than zero")
