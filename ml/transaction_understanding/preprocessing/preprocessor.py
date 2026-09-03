import re
import unicodedata
from typing import Iterable

from .config import PreprocessingConfig
from .schemas import (
    BatchPreprocessingResult,
    PreprocessedTransaction,
    validate_batch,
    validate_text,
)


class TransactionPreprocessor:
    """
    Deterministic text preprocessing for accounting transaction descriptions.

    This component only normalizes text. It does not infer:
    - transaction class
    - account
    - debit/credit
    - payment mode
    """

    _CURRENCY_PATTERNS = (
        (r"\u20b9", "rs "),
        (r"\bINR\b", "rs "),
        (r"\bRs\.\s*", "rs "),
        (r"\bRs\b", "rs "),
        (r"\bRUPEES\b", "rs "),
        (r"\bRupees\b", "rs "),
        (r"\$", "usd "),
        (r"\u20ac", "eur "),
        (r"\u00a3", "gbp "),
    )

    _ACCOUNTING_TERM_MAP = {
        "a/c": "account",
        "a.c.": "account",
        "acct": "account",
        "acc": "account",
        "rec": "received",
        "rcvd": "received",
        "pd": "paid",
        "pmt": "payment",
        "pur": "purchase",
        "purch": "purchase",
        "sal": "sales",
        "exp": "expense",
        "dep": "depreciation",
        "disc": "discount",
        "comm": "commission",
    }

    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def preprocess(self, text: str) -> PreprocessedTransaction:
        original = validate_text(text)
        normalized = original

        if self.config.normalize_unicode:
            normalized = unicodedata.normalize("NFKC", normalized)

        if self.config.lowercase:
            normalized = normalized.lower()

        if self.config.normalize_currency:
            normalized = self._normalize_currency(normalized)

        if self.config.normalize_accounting_terms:
            normalized = self._normalize_accounting_terms(normalized)

        if self.config.normalize_punctuation:
            normalized = self._normalize_punctuation(normalized)

        if self.config.normalize_whitespace:
            normalized = self._normalize_whitespace(normalized)

        return PreprocessedTransaction(
            original_text=original,
            normalized_text=normalized,
        )

    def preprocess_batch(self, texts: Iterable[str]) -> BatchPreprocessingResult:
        values = validate_batch(tuple(texts))
        items = tuple(self.preprocess(text) for text in values)

        return BatchPreprocessingResult(items=items)

    @classmethod
    def _normalize_currency(cls, text: str) -> str:
        result = text

        for pattern, replacement in cls._CURRENCY_PATTERNS:
            result = re.sub(
                pattern,
                replacement,
                result,
                flags=re.IGNORECASE,
            )

        return result

    @classmethod
    def _normalize_accounting_terms(cls, text: str) -> str:
        result = text

        for source, replacement in sorted(
            cls._ACCOUNTING_TERM_MAP.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            result = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                result,
                flags=re.IGNORECASE,
            )

        return result

    @staticmethod
    def _normalize_punctuation(text: str) -> str:
        # Preserve punctuation that is meaningful inside amounts.
        text = re.sub(
            r"(?<!\d)[^\w\s.,%/-]+(?!\d)",
            " ",
            text,
        )

        # Remove separators that are not useful for transaction semantics.
        text = re.sub(r"(?<!\d)[,;:!?]+", " ", text)
        text = re.sub(r"[,;:!?]+(?!\d)", " ", text)

        return text

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()


_default_preprocessor = TransactionPreprocessor()


def preprocess_transaction(text: str) -> str:
    return _default_preprocessor.preprocess(text).normalized_text


def preprocess_transactions(texts: Iterable[str]) -> tuple[str, ...]:
    return _default_preprocessor.preprocess_batch(texts).texts
