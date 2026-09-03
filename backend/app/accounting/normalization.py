from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID


class NormalizationError(ValueError):
    """Raised when transaction data cannot be normalized."""


@dataclass(frozen=True)
class NormalizedTransaction:
    """
    Internal accounting representation of a transaction.

    This object is intentionally independent of SQLAlchemy/FastAPI.
    """

    transaction_id: UUID | None
    transaction_date: date
    description: str
    amount: Decimal

    transaction_type: str | None = None
    debit_account: str | None = None
    credit_account: str | None = None

    @property
    def debit_amount(self) -> Decimal:
        return self.amount

    @property
    def credit_amount(self) -> Decimal:
        return self.amount


def normalize_amount(value: Any) -> Decimal:
    """
    Convert common monetary representations into Decimal.

    Supported examples:
        50000
        "50000"
        "50,000"
        "₹50,000"
        "₹ 50,000.50"
        "50K"
        "1.5L"
    """

    if value is None:
        raise NormalizationError("Amount is required.")

    if isinstance(value, bool):
        raise NormalizationError("Boolean values are not valid amounts.")

    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, int):
        amount = Decimal(value)
    elif isinstance(value, float):
        # Convert through string to avoid binary floating-point artifacts.
        amount = Decimal(str(value))
    elif isinstance(value, str):
        raw = value.strip().upper()

        if not raw:
            raise NormalizationError("Amount cannot be empty.")

        # Remove currency symbols and whitespace.
        raw = (
            raw.replace("₹", "")
            .replace("INR", "")
            .replace("$", "")
            .replace("USD", "")
            .replace(" ", "")
        )

        multiplier = Decimal("1")

        if raw.endswith("K"):
            multiplier = Decimal("1000")
            raw = raw[:-1]

        elif raw.endswith("L"):
            multiplier = Decimal("100000")
            raw = raw[:-1]

        elif raw.endswith("LAKH"):
            multiplier = Decimal("100000")
            raw = raw[:-4]

        elif raw.endswith("M"):
            multiplier = Decimal("1000000")
            raw = raw[:-1]

        # Remove thousands separators.
        raw = raw.replace(",", "")

        # Reject anything that is not a normal numeric representation.
        if not re.fullmatch(r"[+-]?\d+(\.\d+)?", raw):
            raise NormalizationError(
                f"Invalid monetary amount: {value!r}"
            )

        try:
            amount = Decimal(raw) * multiplier
        except InvalidOperation as exc:
            raise NormalizationError(
                f"Invalid monetary amount: {value!r}"
            ) from exc

    else:
        raise NormalizationError(
            f"Unsupported amount type: {type(value).__name__}"
        )

    if not amount.is_finite():
        raise NormalizationError("Amount must be finite.")

    if amount < 0:
        raise NormalizationError("Amount cannot be negative.")

    # Accounting precision: 2 decimal places.
    return amount.quantize(Decimal("0.01"))


def normalize_description(value: Any) -> str:
    """Normalize transaction description."""

    if value is None:
        raise NormalizationError("Transaction description is required.")

    description = str(value).strip()

    if not description:
        raise NormalizationError("Transaction description cannot be empty.")

    # Collapse repeated whitespace.
    description = re.sub(r"\s+", " ", description)

    return description


def normalize_date(value: Any) -> date:
    """Normalize common date representations."""

    if isinstance(value, date):
        return value

    if value is None:
        raise NormalizationError("Transaction date is required.")

    if isinstance(value, str):
        value = value.strip()

        # ISO format.
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass

        # Common Indian/business formats.
        formats = (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%m/%d/%Y",
        )

        from datetime import datetime

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

    raise NormalizationError(
        f"Unsupported transaction date: {value!r}"
    )


def normalize_transaction(
    *,
    transaction_id: UUID | None,
    transaction_date: Any,
    description: Any,
    amount: Any,
    transaction_type: str | None = None,
    debit_account: str | None = None,
    credit_account: str | None = None,
) -> NormalizedTransaction:
    """
    Normalize raw transaction information into the internal
    accounting representation.
    """

    normalized_type = (
        transaction_type.strip().upper()
        if transaction_type
        else None
    )

    normalized_debit = (
        debit_account.strip()
        if debit_account
        else None
    )

    normalized_credit = (
        credit_account.strip()
        if credit_account
        else None
    )

    return NormalizedTransaction(
        transaction_id=transaction_id,
        transaction_date=normalize_date(transaction_date),
        description=normalize_description(description),
        amount=normalize_amount(amount),
        transaction_type=normalized_type,
        debit_account=normalized_debit,
        credit_account=normalized_credit,
    )