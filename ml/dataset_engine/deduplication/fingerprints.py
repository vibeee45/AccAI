from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from typing import Any


def _normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def _normalize_value(value: Any):
    if isinstance(value, Decimal):
        return str(value)

    if is_dataclass(value):
        return {
            key: _normalize_value(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): _normalize_value(item)
            for key, item in sorted(value.items())
        }

    if isinstance(value, (list, tuple)):
        return [
            _normalize_value(item)
            for item in value
        ]

    if isinstance(value, str):
        return _normalize_text(value)

    return value


def record_fingerprint(record: Any) -> str:
    normalized = _normalize_value(record)

    payload = json.dumps(
        normalized,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def semantic_fingerprint(record: Any) -> str:
    """
    Fingerprint accounting meaning while excluding
    the unique transaction identifier.

    This is intentionally NOT used to remove records
    automatically because different natural-language
    variations can represent valuable ML examples.
    """

    normalized = _normalize_value(record)

    if isinstance(normalized, dict):
        normalized.pop("transaction_id", None)
        normalized.pop("variation_id", None)
        normalized.pop("source_transaction_id", None)

    payload = json.dumps(
        normalized,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()
