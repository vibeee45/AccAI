from dataclasses import dataclass


@dataclass(frozen=True)
class AccountingAdapterConfig:
    require_amount: bool = True
    require_valid_accounts: bool = True
    require_valid_directions: bool = True
    require_confidence: bool = True
    minimum_confidence: float = 0.80

    def __post_init__(self) -> None:
        if not isinstance(
            self.require_amount,
            bool,
        ):
            raise TypeError(
                "require_amount must be bool."
            )

        if not isinstance(
            self.require_valid_accounts,
            bool,
        ):
            raise TypeError(
                "require_valid_accounts must be bool."
            )

        if not isinstance(
            self.require_valid_directions,
            bool,
        ):
            raise TypeError(
                "require_valid_directions must be bool."
            )

        if not isinstance(
            self.require_confidence,
            bool,
        ):
            raise TypeError(
                "require_confidence must be bool."
            )

        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0 and 1."
            )
