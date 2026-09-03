from __future__ import annotations

import re
from decimal import Decimal

from .catalog import get_all_templates
from .schemas import AccountingTemplate, TemplateMatch


_TEMPLATE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "cash_sale": (
        "cash sale",
        "cash sales",
        "sold for cash",
    ),
    "credit_sale": (
        "credit sale",
        "credit sales",
        "sold on credit",
    ),
    "cash_purchase": (
        "cash purchase",
        "cash purchases",
        "purchased for cash",
        "purchased goods for cash",
        "purchase goods for cash",
        "cash purchase of goods",
    ),
    "credit_purchase": (
        "credit purchase",
        "credit purchases",
        "purchased on credit",
        "purchased goods on credit",
        "purchase goods on credit",
        "credit purchase of goods",
    ),
    "rent_paid": (
        "rent paid",
        "paid rent",
        "rent expense",
    ),
    "salary_paid": (
        "salary paid",
        "paid salary",
        "salary expense",
    ),
    "electricity_paid": (
        "electricity paid",
        "electricity bill",
        "electricity expense",
    ),
    "transport_paid": (
        "transport paid",
        "transport expense",
        "transportation expense",
    ),
    "commission_received": (
        "commission received",
        "received commission",
    ),
    "interest_received": (
        "interest received",
        "received interest",
    ),
    "capital_introduced": (
        "capital introduced",
        "introduced capital",
        "capital invested",
    ),
    "drawings_cash": (
        "drawings",
        "cash drawings",
        "withdrawn for personal use",
    ),
    "loan_received": (
        "loan received",
        "received loan",
        "borrowed money",
    ),
    "loan_repayment": (
        "loan repayment",
        "repaid loan",
        "loan paid",
    ),
    "cash_deposited_bank": (
        "cash deposited",
        "deposited cash in bank",
        "cash to bank",
    ),
    "cash_withdrawn_bank": (
        "cash withdrawn",
        "withdrawn from bank",
        "bank to cash",
    ),
    "bad_debt": (
        "bad debt",
        "debt written off",
        "receivable written off",
    ),
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_amount(text: str) -> Decimal | None:
    normalized = text.replace(",", "")

    match = re.search(
        r"(?:₹|rs\.?|inr|\$|€|£)?\s*"
        r"(\d+(?:\.\d+)?)",
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return Decimal(match.group(1))


def match_template(transaction_text: str) -> TemplateMatch | None:
    normalized = _normalize_text(transaction_text)

    best_template: AccountingTemplate | None = None
    best_keywords: tuple[str, ...] = ()
    best_score = 0

    for template in get_all_templates():
        keywords = _TEMPLATE_KEYWORDS.get(template.template_id, ())

        matched = tuple(
            keyword
            for keyword in keywords
            if keyword in normalized
        )

        if not matched:
            continue

        score = max(len(keyword) for keyword in matched)

        if score > best_score:
            best_score = score
            best_template = template
            best_keywords = matched

    if best_template is None:
        return None

    confidence = min(
        Decimal("0.99"),
        Decimal("0.50") + (Decimal(best_score) / Decimal("100")),
    )

    return TemplateMatch(
        template_id=best_template.template_id,
        confidence=confidence,
        matched_keywords=best_keywords,
    )


def resolve_template(transaction_text: str) -> AccountingTemplate:
    match = match_template(transaction_text)

    if match is None:
        raise LookupError(
            f"No accounting template matched transaction: {transaction_text!r}"
        )

    for template in get_all_templates():
        if template.template_id == match.template_id:
            return template

    raise LookupError(
        f"Template {match.template_id!r} could not be resolved."
    )
