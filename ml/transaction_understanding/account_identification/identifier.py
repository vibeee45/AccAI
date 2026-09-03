import re

from .account_catalog import AccountCatalog
from .config import AccountIdentificationConfig
from .features import AccountTextFeatures
from .schemas import (
    AccountCandidate,
    AccountIdentificationResult,
)


class AccountIdentifier:
    """
    Identifies the most likely accounting account for a transaction.

    The identifier combines:
    - TF-IDF similarity
    - exact/phrase keyword matching
    - transaction-class hints

    It does NOT decide debit/credit.
    """

    _CLASS_HINTS = {
        "sales": (
            "sales",
            "sold",
            "customer",
            "revenue",
        ),
        "purchase": (
            "purchase",
            "purchased",
            "bought",
            "inventory",
            "supplier",
        ),
        "rent": (
            "rent",
            "rental",
        ),
        "salary": (
            "salary",
            "salaries",
            "wages",
            "employee",
            "staff",
        ),
        "utilities": (
            "electricity",
            "water",
            "gas",
            "utility",
            "utilities",
        ),
        "transport": (
            "transport",
            "freight",
            "delivery",
            "shipping",
        ),
        "advertising": (
            "advertising",
            "marketing",
            "promotion",
            "campaign",
        ),
        "commission": (
            "commission",
        ),
        "interest": (
            "interest",
        ),
        "cash_deposit": (
            "cash deposited",
            "cash deposit",
            "deposited cash",
        ),
        "cash_withdrawal": (
            "cash withdrawal",
            "cash withdrawn",
            "withdrew cash",
        ),
        "bank_transfer": (
            "bank transfer",
            "transferred",
            "neft",
            "rtgs",
            "imps",
            "upi",
        ),
        "capital_introduction": (
            "capital",
            "owner investment",
            "introduced capital",
        ),
        "loan": (
            "loan",
            "borrowed",
            "borrowing",
        ),
        "asset_purchase": (
            "purchased machinery",
            "purchased furniture",
            "purchased equipment",
            "bought computer",
            "fixed asset",
        ),
        "asset_sale": (
            "sold machinery",
            "sold furniture",
            "sold equipment",
            "fixed asset sale",
        ),
        "tax": (
            "tax",
            "gst",
        ),
        "insurance": (
            "insurance",
            "premium",
        ),
        "miscellaneous_income": (
            "other income",
            "miscellaneous income",
            "dividend income",
        ),
        "miscellaneous_expense": (
            "other expense",
            "miscellaneous expense",
        ),
    }

    def __init__(
        self,
        catalog: AccountCatalog | None = None,
        config: AccountIdentificationConfig | None = None,
    ) -> None:
        self.catalog = catalog or AccountCatalog()

        self.config = (
            config
            or AccountIdentificationConfig()
        )

        self.features = AccountTextFeatures(
            ngram_range=(
                self.config.ngram_min,
                self.config.ngram_max,
            ),
            min_df=self.config.min_df,
            max_features=self.config.max_features,
        )

        self._fit_features()

    def _fit_features(self) -> None:
        texts = [
            self._account_document(account)
            for account in self.catalog.accounts
        ]

        self.features.fit(texts)

    @staticmethod
    def _account_document(account) -> str:
        return " ".join(
            (
                account.account_name,
                account.category,
                *account.keywords,
            )
        )

    def identify(
        self,
        transaction_text: str,
        transaction_class: str | None = None,
    ) -> AccountIdentificationResult:
        if not isinstance(
            transaction_text,
            str,
        ):
            raise TypeError(
                "transaction_text must be a string."
            )

        transaction_text = transaction_text.strip()

        if not transaction_text:
            raise ValueError(
                "transaction_text cannot be empty."
            )

        accounts = self.catalog.accounts

        account_documents = [
            self._account_document(account)
            for account in accounts
        ]

        similarities = self.features.similarity(
            transaction_text,
            account_documents,
        )

        scored_accounts = []

        for account, similarity in zip(
            accounts,
            similarities,
        ):
            keyword_score = self._keyword_score(
                transaction_text,
                account,
            )

            class_bonus = self._class_bonus(
                transaction_text,
                account,
                transaction_class,
            ) if transaction_class else 0.0

            # Base semantic similarity.
            #
            # Explicit keyword matches receive a stronger
            # weight because accounting account names often
            # have very specific vocabulary.
            score = (
                (similarity * 0.55)
                + (keyword_score * 0.35)
                + (class_bonus * 0.10)
            )

            # A strong exact keyword match should receive
            # an additional precision boost.
            if keyword_score >= 0.90:
                score += 0.20

            score = min(
                max(score, 0.0),
                1.0,
            )

            scored_accounts.append(
                (
                    account,
                    score,
                )
            )

        scored_accounts.sort(
            key=lambda item: (
                -item[1],
                item[0].account_name,
            )
        )

        selected = [
            item
            for item in scored_accounts
            if item[1] >= self.config.min_similarity
        ][: self.config.top_k]

        candidates = tuple(
            AccountCandidate(
                account_id=account.account_id,
                account_name=account.account_name,
                category=account.category,
                score=round(
                    score,
                    6,
                ),
                rank=index,
            )
            for index, (
                account,
                score,
            ) in enumerate(
                selected,
                start=1,
            )
        )

        if not candidates:
            return AccountIdentificationResult(
                transaction_text=transaction_text,
                candidates=(),
                selected_account_id=None,
                selected_account_name=None,
                confidence=0.0,
                requires_review=True,
            )

        best = candidates[0]

        return AccountIdentificationResult(
            transaction_text=transaction_text,
            candidates=candidates,
            selected_account_id=best.account_id,
            selected_account_name=best.account_name,
            confidence=best.score,
            requires_review=(
                best.score
                < self.config.confidence_threshold
            ),
        )

    def identify_many(
        self,
        transactions: list[str],
        transaction_class: str | None = None,
    ) -> list[AccountIdentificationResult]:
        if not transactions:
            raise ValueError(
                "transactions cannot be empty."
            )

        return [
            self.identify(
                transaction,
                transaction_class=transaction_class,
            )
            for transaction in transactions
        ]

    @staticmethod
    def _keyword_score(
        transaction_text: str,
        account,
    ) -> float:
        """
        Calculate explicit keyword matching strength.

        Exact phrases are given priority over generic
        semantic similarity.
        """

        text = transaction_text.lower()

        best_score = 0.0

        for keyword in account.keywords:
            normalized_keyword = keyword.lower().strip()

            if not normalized_keyword:
                continue

            # Exact phrase/keyword occurrence.
            if re.search(
                r"(?<!\w)"
                + re.escape(normalized_keyword)
                + r"(?!\w)",
                text,
            ):
                word_count = len(
                    normalized_keyword.split()
                )

                if word_count >= 3:
                    score = 1.0
                elif word_count == 2:
                    score = 0.95
                else:
                    score = 0.90

                best_score = max(
                    best_score,
                    score,
                )

        # Account name itself is also a strong signal.
        account_name = (
            account.account_name
            .lower()
            .strip()
        )

        if account_name and re.search(
            r"(?<!\w)"
            + re.escape(account_name)
            + r"(?!\w)",
            text,
        ):
            best_score = max(
                best_score,
                1.0,
            )

        return best_score

    def _class_bonus(
        self,
        transaction_text: str,
        account,
        transaction_class: str,
    ) -> float:
        hints = self._CLASS_HINTS.get(
            transaction_class.lower(),
            (),
        )

        if not hints:
            return 0.0

        text = transaction_text.lower()

        account_text = self._account_document(
            account
        ).lower()

        matched_hints = sum(
            1
            for hint in hints
            if re.search(
                r"(?<!\w)"
                + re.escape(hint.lower())
                + r"(?!\w)",
                text,
            )
        )

        if matched_hints == 0:
            return 0.0

        account_matches = sum(
            1
            for hint in hints
            if hint.lower() in account_text
        )

        if account_matches == 0:
            return 0.0

        return min(
            self.config.class_bonus,
            self.config.class_bonus
            * (
                account_matches
                / len(hints)
            ),
        )

    def vocabulary_size(self) -> int:
        return self.features.vocabulary_size()
