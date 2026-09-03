from dataclasses import dataclass, field


DEFAULT_ACCOUNT_CATEGORIES = (
    "asset",
    "liability",
    "capital",
    "income",
    "expense",
)


@dataclass(frozen=True)
class AccountIdentificationConfig:
    """
    Configuration for accounting account identification.
    """

    account_categories: tuple[str, ...] = field(
        default_factory=lambda: DEFAULT_ACCOUNT_CATEGORIES
    )

    top_k: int = 3

    confidence_threshold: float = 0.70

    min_similarity: float = 0.0

    ngram_min: int = 1
    ngram_max: int = 2

    min_df: int = 1
    max_features: int | None = 50000

    class_bonus: float = 0.15

    def __post_init__(self) -> None:
        if not self.account_categories:
            raise ValueError(
                "At least one account category is required."
            )

        if len(set(self.account_categories)) != len(
            self.account_categories
        ):
            raise ValueError(
                "Account categories must be unique."
            )

        if self.top_k < 1:
            raise ValueError(
                "top_k must be at least 1."
            )

        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError(
                "confidence_threshold must be between 0 and 1."
            )

        if not 0 <= self.min_similarity <= 1:
            raise ValueError(
                "min_similarity must be between 0 and 1."
            )

        if self.ngram_min < 1:
            raise ValueError(
                "ngram_min must be at least 1."
            )

        if self.ngram_max < self.ngram_min:
            raise ValueError(
                "ngram_max must be >= ngram_min."
            )

        if self.min_df < 1:
            raise ValueError(
                "min_df must be at least 1."
            )

        if not 0 <= self.class_bonus <= 1:
            raise ValueError(
                "class_bonus must be between 0 and 1."
            )
