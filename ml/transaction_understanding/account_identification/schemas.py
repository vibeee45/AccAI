from dataclasses import dataclass


@dataclass(frozen=True)
class AccountRecord:
    """
    Represents one account in the account catalog.
    """

    account_id: str
    account_name: str
    category: str
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name.strip():
            raise ValueError(
                "account_name cannot be empty."
            )

        if not self.category.strip():
            raise ValueError(
                "category cannot be empty."
            )

        if len(
            set(keyword.lower() for keyword in self.keywords)
        ) != len(self.keywords):
            raise ValueError(
                "Account keywords must be unique."
            )


@dataclass(frozen=True)
class AccountCandidate:
    """
    Ranked candidate account.
    """

    account_id: str
    account_name: str
    category: str
    score: float
    rank: int

    def __post_init__(self) -> None:
        if not self.account_id:
            raise ValueError(
                "account_id cannot be empty."
            )

        if not self.account_name:
            raise ValueError(
                "account_name cannot be empty."
            )

        if not 0 <= self.score <= 1:
            raise ValueError(
                "score must be between 0 and 1."
            )

        if self.rank < 1:
            raise ValueError(
                "rank must be at least 1."
            )


@dataclass(frozen=True)
class AccountIdentificationResult:
    """
    Result returned by account identification.
    """

    transaction_text: str
    candidates: tuple[AccountCandidate, ...]
    selected_account_id: str | None
    selected_account_name: str | None
    confidence: float
    requires_review: bool

    def __post_init__(self) -> None:
        if not self.transaction_text.strip():
            raise ValueError(
                "transaction_text cannot be empty."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not self.candidates:
            if self.selected_account_id is not None:
                raise ValueError(
                    "selected_account_id cannot exist without candidates."
                )

            if self.selected_account_name is not None:
                raise ValueError(
                    "selected_account_name cannot exist without candidates."
                )

        if self.candidates:
            if self.selected_account_id is None:
                raise ValueError(
                    "selected_account_id is required when candidates exist."
                )

            if self.selected_account_name is None:
                raise ValueError(
                    "selected_account_name is required when candidates exist."
                )
