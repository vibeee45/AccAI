from dataclasses import dataclass


@dataclass(frozen=True)
class JournalGenerationConfig:
    require_positive_amount: bool = True
    require_distinct_accounts: bool = True
    generate_narration: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.require_positive_amount, bool):
            raise TypeError(
                "require_positive_amount must be bool."
            )

        if not isinstance(self.require_distinct_accounts, bool):
            raise TypeError(
                "require_distinct_accounts must be bool."
            )

        if not isinstance(self.generate_narration, bool):
            raise TypeError(
                "generate_narration must be bool."
            )
