from dataclasses import dataclass


@dataclass(frozen=True)
class RuleValidationConfig:
    require_distinct_accounts: bool = True
    require_positive_amount: bool = True
    require_balanced_entry: bool = True
    confidence_threshold: float = 0.80

    def __post_init__(self) -> None:
        if not isinstance(
            self.require_distinct_accounts,
            bool,
        ):
            raise TypeError(
                "require_distinct_accounts must be bool."
            )

        if not isinstance(
            self.require_positive_amount,
            bool,
        ):
            raise TypeError(
                "require_positive_amount must be bool."
            )

        if not isinstance(
            self.require_balanced_entry,
            bool,
        ):
            raise TypeError(
                "require_balanced_entry must be bool."
            )

        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(
                "confidence_threshold must be between 0 and 1."
            )
