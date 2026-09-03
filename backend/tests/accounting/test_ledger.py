from decimal import Decimal

import pytest

from app.accounting.journal import generate_journal
from app.accounting.ledger import (
    AccountLedger,
    LedgerBook,
    get_account_balance,
    get_trial_balance_totals,
    post_journal_to_ledger,
    post_journals_to_ledger,
)
from app.accounting.normalization import normalize_transaction


def make_transaction(
    description: str,
    amount: str,
    debit_account: str,
    credit_account: str,
):
    return normalize_transaction(
        transaction_id=None,
        transaction_date="2026-09-03",
        description=description,
        amount=amount,
        debit_account=debit_account,
        credit_account=credit_account,
    )


def test_single_journal_posts_to_two_ledgers():
    transaction = make_transaction(
        "Purchased goods for cash",
        "50000",
        "Purchases",
        "Cash",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journal_to_ledger(
        LedgerBook(),
        journal,
    )

    purchases = ledger_book.get_account("Purchases")
    cash = ledger_book.get_account("Cash")

    assert purchases is not None
    assert cash is not None

    assert purchases.total_debit == Decimal("50000.00")
    assert purchases.total_credit == Decimal("0.00")

    assert cash.total_debit == Decimal("0.00")
    assert cash.total_credit == Decimal("50000.00")


def test_debit_account_has_debit_balance():
    transaction = make_transaction(
        "Purchased goods for cash",
        "50000",
        "Purchases",
        "Cash",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journal_to_ledger(
        LedgerBook(),
        journal,
    )

    purchases = ledger_book.get_account("Purchases")

    assert purchases is not None
    assert purchases.balance == Decimal("50000.00")
    assert purchases.debit_balance == Decimal("50000.00")
    assert purchases.credit_balance == Decimal("0.00")
    assert purchases.balance_type == "DEBIT"


def test_credit_account_has_credit_balance():
    transaction = make_transaction(
        "Purchased goods for cash",
        "50000",
        "Purchases",
        "Cash",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journal_to_ledger(
        LedgerBook(),
        journal,
    )

    cash = ledger_book.get_account("Cash")

    assert cash is not None
    assert cash.balance == Decimal("-50000.00")
    assert cash.debit_balance == Decimal("0.00")
    assert cash.credit_balance == Decimal("50000.00")
    assert cash.balance_type == "CREDIT"


def test_multiple_journals_are_grouped_by_account():
    transactions = [
        make_transaction(
            "Capital introduced",
            "100000",
            "Cash",
            "Capital",
        ),
        make_transaction(
            "Purchased goods",
            "30000",
            "Purchases",
            "Cash",
        ),
        make_transaction(
            "Cash sales",
            "50000",
            "Cash",
            "Sales",
        ),
    ]

    journals = [
        generate_journal(transaction)
        for transaction in transactions
    ]

    ledger_book = post_journals_to_ledger(journals)

    cash = ledger_book.get_account("Cash")
    capital = ledger_book.get_account("Capital")
    purchases = ledger_book.get_account("Purchases")
    sales = ledger_book.get_account("Sales")

    assert cash is not None
    assert capital is not None
    assert purchases is not None
    assert sales is not None

    assert cash.total_debit == Decimal("150000.00")
    assert cash.total_credit == Decimal("30000.00")

    assert cash.balance == Decimal("120000.00")

    assert capital.balance == Decimal("-100000.00")

    assert purchases.balance == Decimal("30000.00")

    assert sales.balance == Decimal("-50000.00")


def test_ledger_total_debits_equal_total_credits():
    transactions = [
        make_transaction(
            "Capital introduced",
            "100000",
            "Cash",
            "Capital",
        ),
        make_transaction(
            "Purchased goods",
            "30000",
            "Purchases",
            "Cash",
        ),
        make_transaction(
            "Cash sales",
            "50000",
            "Cash",
            "Sales",
        ),
    ]

    journals = [
        generate_journal(transaction)
        for transaction in transactions
    ]

    ledger_book = post_journals_to_ledger(journals)

    assert ledger_book.total_debit == Decimal("180000.00")
    assert ledger_book.total_credit == Decimal("180000.00")


def test_account_balance_helper():
    transaction = make_transaction(
        "Paid salary",
        "10000",
        "Salary",
        "Cash",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journal_to_ledger(
        LedgerBook(),
        journal,
    )

    assert get_account_balance(
        ledger_book,
        "Salary",
    ) == Decimal("10000.00")

    assert get_account_balance(
        ledger_book,
        "Cash",
    ) == Decimal("-10000.00")


def test_missing_account_returns_zero_balance():
    ledger_book = LedgerBook()

    assert get_account_balance(
        ledger_book,
        "Cash",
    ) == Decimal("0.00")


def test_account_names_are_sorted():
    ledger_book = LedgerBook()

    ledger_book.get_or_create("Sales")
    ledger_book.get_or_create("Cash")
    ledger_book.get_or_create("Purchases")

    assert ledger_book.account_names() == [
        "Cash",
        "Purchases",
        "Sales",
    ]


def test_empty_ledger_has_zero_totals():
    ledger_book = LedgerBook()

    assert ledger_book.total_debit == Decimal("0.00")
    assert ledger_book.total_credit == Decimal("0.00")

    debit, credit = get_trial_balance_totals(ledger_book)

    assert debit == Decimal("0.00")
    assert credit == Decimal("0.00")


def test_ledger_line_rejects_both_debit_and_credit():
    ledger = AccountLedger("Cash")

    with pytest.raises(ValueError):
        ledger.add_line(
            date="2026-09-03",
            description="Invalid",
            debit=Decimal("100.00"),
            credit=Decimal("50.00"),
        )


def test_ledger_line_rejects_zero_amount():
    ledger = AccountLedger("Cash")

    with pytest.raises(ValueError):
        ledger.add_line(
            date="2026-09-03",
            description="Invalid",
            debit=Decimal("0.00"),
            credit=Decimal("0.00"),
        )


def test_unbalanced_journal_cannot_be_posted():
    transaction = make_transaction(
        "Valid transaction",
        "50000",
        "Purchases",
        "Cash",
    )

    journal = generate_journal(transaction)

    # Deliberately corrupt the journal for this test.
    object.__setattr__(
        journal.lines[0],
        "debit",
        Decimal("40000.00"),
    )

    with pytest.raises(ValueError):
        post_journal_to_ledger(
            LedgerBook(),
            journal,
        )