from .config import AccountIdentificationConfig
from .identifier import AccountIdentifier
from .schemas import AccountIdentificationResult


class AccountIdentificationService:
    """
    Application-facing service for account identification.
    """

    def __init__(
        self,
        identifier: AccountIdentifier | None = None,
    ) -> None:
        self.identifier = (
            identifier
            or AccountIdentifier(
                config=AccountIdentificationConfig()
            )
        )

    def identify(
        self,
        transaction_text: str,
        transaction_class: str | None = None,
    ) -> AccountIdentificationResult:
        return self.identifier.identify(
            transaction_text,
            transaction_class=transaction_class,
        )

    def identify_many(
        self,
        transactions: list[str],
        transaction_class: str | None = None,
    ) -> list[AccountIdentificationResult]:
        return self.identifier.identify_many(
            transactions,
            transaction_class=transaction_class,
        )

    @property
    def ready(self) -> bool:
        return (
            self.identifier.vocabulary_size()
            > 0
        )
