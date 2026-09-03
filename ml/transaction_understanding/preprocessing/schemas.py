from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PreprocessedTransaction:
    original_text: str
    normalized_text: str


@dataclass(frozen=True)
class BatchPreprocessingResult:
    items: tuple[PreprocessedTransaction, ...]

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(item.normalized_text for item in self.items)


def validate_text(value: object) -> str:
    if value is None:
        raise ValueError("Transaction text cannot be None.")

    if not isinstance(value, str):
        raise TypeError("Transaction text must be a string.")

    if not value.strip():
        raise ValueError("Transaction text cannot be empty.")

    return value


def validate_batch(values: Sequence[str]) -> tuple[str, ...]:
    if values is None:
        raise ValueError("Transaction batch cannot be None.")

    return tuple(validate_text(value) for value in values)
