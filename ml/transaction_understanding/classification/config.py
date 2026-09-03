from dataclasses import dataclass, field


DEFAULT_TRANSACTION_CLASSES = (
    "sales",
    "purchase",
    "rent",
    "salary",
    "utilities",
    "transport",
    "advertising",
    "commission",
    "interest",
    "cash_deposit",
    "cash_withdrawal",
    "bank_transfer",
    "capital_introduction",
    "loan",
    "asset_purchase",
    "asset_sale",
    "tax",
    "insurance",
    "miscellaneous_income",
    "miscellaneous_expense",
)


@dataclass(frozen=True)
class ClassificationConfig:
    classes: tuple[str, ...] = field(
        default_factory=lambda: DEFAULT_TRANSACTION_CLASSES
    )

    test_size: float = 0.20
    random_state: int = 42

    min_df: int = 1
    max_features: int | None = 50000
    ngram_min: int = 1
    ngram_max: int = 2

    classifier_c: float = 2.0
    max_iter: int = 2000

    confidence_threshold: float = 0.70

    def __post_init__(self) -> None:
        if not self.classes:
            raise ValueError(
                "At least one transaction class is required."
            )

        if len(set(self.classes)) != len(self.classes):
            raise ValueError(
                "Transaction classes must be unique."
            )

        if not 0 < self.test_size < 1:
            raise ValueError(
                "test_size must be between 0 and 1."
            )

        if self.min_df < 1:
            raise ValueError(
                "min_df must be at least 1."
            )

        if self.ngram_min < 1:
            raise ValueError(
                "ngram_min must be at least 1."
            )

        if self.ngram_max < self.ngram_min:
            raise ValueError(
                "ngram_max must be >= ngram_min."
            )

        if self.classifier_c <= 0:
            raise ValueError(
                "classifier_c must be greater than 0."
            )

        if self.max_iter < 1:
            raise ValueError(
                "max_iter must be positive."
            )

        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError(
                "confidence_threshold must be between 0 and 1."
            )
