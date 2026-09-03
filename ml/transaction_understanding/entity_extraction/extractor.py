import re
from decimal import Decimal, InvalidOperation
from typing import Iterable

from .config import EntityExtractionConfig
from .schemas import (
    EntityExtractionResult,
    EntityType,
    ExtractedEntity,
)


class TransactionEntityExtractor:
    """
    Deterministic entity extraction for accounting transactions.

    This component extracts information from transaction text.
    It does NOT decide:
    - transaction classification
    - accounting treatment
    - debit/credit
    - final ledger account
    """

    _DATE_PATTERNS = (
        re.compile(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        ),
        re.compile(
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"
        ),
    )

    _AMOUNT_PATTERN = re.compile(
        r"(?<![\w])"
        r"(?:"
        r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?"
        r"|"
        r"\d+(?:\.\d+)?"
        r")"
        r"(?![\w])"
    )

    _CURRENCY_PATTERNS = (
        (re.compile(r"\brupees?\b", re.IGNORECASE), "INR"),
        (re.compile(r"\binr\b", re.IGNORECASE), "INR"),
        (re.compile(r"\brs\.?\b", re.IGNORECASE), "INR"),
        (re.compile(r"\u20b9"), "INR"),
        (re.compile(r"\busd\b", re.IGNORECASE), "USD"),
        (re.compile(r"\$"), "USD"),
        (re.compile(r"\beur\b", re.IGNORECASE), "EUR"),
        (re.compile(r"\u20ac"), "EUR"),
        (re.compile(r"\bgbp\b", re.IGNORECASE), "GBP"),
        (re.compile(r"\u00a3"), "GBP"),
    )

    _PAYMENT_PATTERNS = (
        ("upi", re.compile(r"\bupi\b", re.IGNORECASE)),
        ("neft", re.compile(r"\bneft\b", re.IGNORECASE)),
        ("rtgs", re.compile(r"\brtgs\b", re.IGNORECASE)),
        ("imps", re.compile(r"\bimps\b", re.IGNORECASE)),
        ("cash", re.compile(r"\bcash\b", re.IGNORECASE)),
        ("cheque", re.compile(r"\bcheque\b", re.IGNORECASE)),
        ("check", re.compile(r"\bcheck\b", re.IGNORECASE)),
        (
            "credit_card",
            re.compile(r"\bcredit\s+card\b", re.IGNORECASE),
        ),
        (
            "debit_card",
            re.compile(r"\bdebit\s+card\b", re.IGNORECASE),
        ),
        (
            "card",
            re.compile(r"\bcard\b", re.IGNORECASE),
        ),
        (
            "bank_transfer",
            re.compile(
                r"\bbank\s+transfer\b",
                re.IGNORECASE,
            ),
        ),
    )

    # Explicitly handles:
    #
    # account 123456
    # account no 123456
    # account no. 123456
    # account number 123456
    # acct 123456
    # acct no 123456
    # a/c 123456
    # a/c no 123456
    # a/c number 123456
    #
    # The account identifier is captured separately from
    # the label.
    _ACCOUNT_REFERENCE_PATTERN = re.compile(
        r"\b"
        r"(?:account|acct|a/c)"
        r"(?:"
        r"\s+(?:no|number)"
        r"\.?"
        r")?"
        r"\s*[:#-]?"
        r"\s*"
        r"(?P<account_number>"
        r"[A-Za-z0-9]"
        r"[A-Za-z0-9/-]*"
        r")"
        r"\b",
        re.IGNORECASE,
    )

    _DESCRIPTION_MARKERS = (
        "for",
        "towards",
        "against",
        "regarding",
        "being",
    )

    def __init__(
        self,
        config: EntityExtractionConfig | None = None,
    ) -> None:
        self.config = config or EntityExtractionConfig()

    def extract(
        self,
        text: str,
    ) -> EntityExtractionResult:
        if text is None:
            raise ValueError(
                "Transaction text cannot be None."
            )

        if not isinstance(text, str):
            raise TypeError(
                "Transaction text must be a string."
            )

        if not text.strip():
            raise ValueError(
                "Transaction text cannot be empty."
            )

        entities: list[ExtractedEntity] = []

        if self.config.extract_dates:
            entities.extend(
                self._extract_dates(text)
            )

        if self.config.extract_amounts:
            entities.extend(
                self._extract_amounts(text)
            )

        if self.config.extract_currencies:
            entities.extend(
                self._extract_currencies(text)
            )

        if self.config.extract_payment_references:
            entities.extend(
                self._extract_payment_references(text)
            )

        # Account references are extracted before the
        # generic amount entities are resolved.
        entities.extend(
            self._extract_account_references(text)
        )

        if self.config.extract_people:
            entities.extend(
                self._extract_people(text)
            )

        if self.config.extract_organizations:
            entities.extend(
                self._extract_organizations(text)
            )

        if self.config.extract_descriptions:
            entities.extend(
                self._extract_descriptions(text)
            )

        # An account number is not a transaction amount.
        entities = self._remove_amounts_inside_accounts(
            entities
        )

        entities = self._remove_overlapping_entities(
            entities
        )

        entities.sort(
            key=lambda entity: (
                entity.start,
                entity.end,
            )
        )

        return EntityExtractionResult(
            original_text=text,
            entities=tuple(entities),
        )

    def extract_batch(
        self,
        texts: Iterable[str],
    ) -> tuple[EntityExtractionResult, ...]:
        if texts is None:
            raise ValueError(
                "Transaction batch cannot be None."
            )

        return tuple(
            self.extract(text)
            for text in texts
        )

    def _extract_amounts(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        for match in self._AMOUNT_PATTERN.finditer(text):
            raw = match.group(0)

            if self._looks_like_date_component(
                text,
                match.start(),
                match.end(),
            ):
                continue

            try:
                value = Decimal(
                    raw.replace(",", "")
                )
            except InvalidOperation:
                continue

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.AMOUNT,
                    text=raw,
                    normalized_value=str(value),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.99,
                )
            )

        return entities

    def _extract_dates(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        for pattern in self._DATE_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(0)

                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DATE,
                        text=raw,
                        normalized_value=raw,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.99,
                    )
                )

        return entities

    def _extract_currencies(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        for pattern, normalized in self._CURRENCY_PATTERNS:
            for match in pattern.finditer(text):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.CURRENCY,
                        text=match.group(0),
                        normalized_value=normalized,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.99,
                    )
                )

        return entities

    def _extract_payment_references(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        for normalized, pattern in self._PAYMENT_PATTERNS:
            for match in pattern.finditer(text):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.PAYMENT_REFERENCE,
                        text=match.group(0),
                        normalized_value=normalized,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.98,
                    )
                )

        return entities

    def _extract_account_references(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        for match in self._ACCOUNT_REFERENCE_PATTERN.finditer(
            text
        ):
            account_number = match.group(
                "account_number"
            ).strip()

            # Account references should contain at least
            # one digit. This prevents ordinary words such
            # as "account balance" from becoming references.
            if not any(
                character.isdigit()
                for character in account_number
            ):
                continue

            full_text = match.group(0).strip()

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.ACCOUNT_REFERENCE,
                    text=full_text,
                    normalized_value=account_number.lower(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.995,
                )
            )

        return entities

    def _extract_people(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        pattern = re.compile(
            r"\b(?:to|from|paid\s+to|received\s+from)\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            value = match.group(1).strip()

            if self._looks_like_non_person(value):
                continue

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.PERSON,
                    text=value,
                    normalized_value=value.lower(),
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.78,
                )
            )

        return entities

    def _extract_organizations(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        pattern = re.compile(
            r"\b("
            r"[A-Z][A-Za-z0-9&.-]*"
            r"(?:\s+[A-Z][A-Za-z0-9&.-]*)*"
            r"\s+(?:Ltd|Limited|LLP|Pvt|Private|Inc|Corp|Corporation)"
            r")\b",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            value = match.group(1).strip()

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.ORGANIZATION,
                    text=value,
                    normalized_value=value.lower(),
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.90,
                )
            )

        return entities

    def _extract_descriptions(
        self,
        text: str,
    ) -> list[ExtractedEntity]:
        entities = []

        marker_pattern = "|".join(
            re.escape(marker)
            for marker in self._DESCRIPTION_MARKERS
        )

        pattern = re.compile(
            rf"\b(?:{marker_pattern})\b\s+"
            r"(.+?)(?="
            r"\s+\b(?:through|via|using|on|dated)\b"
            r"|$)",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            value = match.group(1).strip(
                " .,:;"
            )

            if not value:
                continue

            if value.lower() in {
                normalized
                for normalized, _ in self._PAYMENT_PATTERNS
            }:
                continue

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.DESCRIPTION,
                    text=value,
                    normalized_value=value.lower(),
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.75,
                )
            )

        return entities

    @staticmethod
    def _remove_amounts_inside_accounts(
        entities: list[ExtractedEntity],
    ) -> list[ExtractedEntity]:
        account_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == EntityType.ACCOUNT_REFERENCE
        ]

        if not account_entities:
            return entities

        filtered = []

        for entity in entities:
            if entity.entity_type != EntityType.AMOUNT:
                filtered.append(entity)
                continue

            inside_account = any(
                account.start <= entity.start
                and entity.end <= account.end
                for account in account_entities
            )

            if not inside_account:
                filtered.append(entity)

        return filtered

    @staticmethod
    def _looks_like_date_component(
        text: str,
        start: int,
        end: int,
    ) -> bool:
        surrounding = text[
            max(0, start - 3):
            min(len(text), end + 3)
        ]

        return bool(
            re.search(
                r"\d{1,4}[/-]\d{1,4}[/-]?$|"
                r"^\d{1,4}[/-]\d{1,4}",
                surrounding,
            )
        )

    @staticmethod
    def _looks_like_non_person(
        value: str,
    ) -> bool:
        excluded = {
            "office rent",
            "bank transfer",
            "credit card",
            "debit card",
            "cash payment",
        }

        return value.lower() in excluded

    @staticmethod
    def _remove_overlapping_entities(
        entities: list[ExtractedEntity],
    ) -> list[ExtractedEntity]:
        """
        Remove overlapping lower-confidence entities.

        Higher-confidence entities take precedence.
        """

        ordered = sorted(
            entities,
            key=lambda entity: (
                -entity.confidence,
                entity.start,
                -(entity.end - entity.start),
            ),
        )

        accepted: list[ExtractedEntity] = []

        for entity in ordered:
            overlaps = any(
                entity.start < existing.end
                and entity.end > existing.start
                for existing in accepted
            )

            if not overlaps:
                accepted.append(entity)

        return accepted


_default_extractor = TransactionEntityExtractor()


def extract_entities(
    text: str,
) -> EntityExtractionResult:
    return _default_extractor.extract(text)


def extract_entities_batch(
    texts: Iterable[str],
) -> tuple[EntityExtractionResult, ...]:
    return _default_extractor.extract_batch(texts)
