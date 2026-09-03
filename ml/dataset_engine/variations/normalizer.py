from __future__ import annotations

import re


def normalize_variation(text: str) -> str:
    normalized = text.strip().lower()

    # Normalize currency markers.
    normalized = re.sub(r"\brs\.?\s*", "rs ", normalized)
    normalized = re.sub(r"\binr\b\s*", "rs ", normalized)

    # Normalize whitespace.
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def normalize_for_comparison(text: str) -> str:
    normalized = normalize_variation(text)

    # Normalize currency symbols.
    normalized = re.sub(r"[₹$€£]", "", normalized)

    # Normalize numeric amounts, including comma-separated values.
    normalized = re.sub(
        r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b",
        "<amount>",
        normalized,
    )

    normalized = re.sub(
        r"\b\d+(?:\.\d+)?\b",
        "<amount>",
        normalized,
    )

    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()
