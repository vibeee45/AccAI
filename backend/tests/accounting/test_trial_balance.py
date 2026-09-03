from decimal import Decimal

from app.accounting.journal import generate_journal
from app.accounting.ledger import (
    LedgerBook,
    post_journals_to_ledger,
)
from app.accounting.normalization import normalize_transaction
from app.accounting.trial_balance import (
    generate_trial_balance,
    get_trial_balance_row,
)


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


def test_trial_balance_from_single_transaction():
    transaction = make_transaction(
        "Purchased goods for cash",
        "50000",
        "Purchases",
        "Cash",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journals_to_ledger([journal])

    trial_balance = generate_trial_balance(ledger_book)

    assert trial_balance.account_count == 2

    assert trial_balance.total_debit == Decimal("50000.00")
    assert trial_balance.total_credit == Decimal("50000.00")

    assert trial_balance.is_balanced is True
    assert trial_balance.difference == Decimal("0.00")


def test_trial_balance_multiple_transactions():
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
        make_transaction(
            "Salary paid",
            "10000",
            "Salary",
            "Cash",
        ),
    ]

    journals = [
        generate_journal(transaction)
        for transaction in transactions
    ]

    ledger_book = post_journals_to_ledger(journals)

    trial_balance = generate_trial_balance(ledger_book)

    assert trial_balance.is_balanced is True

    assert trial_balance.total_debit == Decimal("150000.00")
    assert trial_balance.total_credit == Decimal("150000.00")


def test_cash_row_has_debit_balance():
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

    trial_balance = generate_trial_balance(ledger_book)

    cash = get_trial_balance_row(
        trial_balance,
        "Cash",
    )

    assert cash is not None
    assert cash.debit == Decimal("120000.00")
    assert cash.credit == Decimal("0.00")


def test_capital_row_has_credit_balance():
    transaction = make_transaction(
        "Capital introduced",
        "100000",
        "Cash",
        "Capital",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journals_to_ledger([journal])

    trial_balance = generate_trial_balance(ledger_book)

    capital = get_trial_balance_row(
        trial_balance,
        "Capital",
    )

    assert capital is not None
    assert capital.debit == Decimal("0.00")
    assert capital.credit == Decimal("100000.00")


def test_zero_balance_accounts_are_excluded():
    ledger_book = LedgerBook()

    cash = ledger_book.get_or_create("Cash")

    cash.add_line(
        date="2026-09-03",
        description="Cash received",
        debit=Decimal("10000.00"),
    )

    cash.add_line(
        date="2026-09-03",
        description="Cash paid",
        credit=Decimal("10000.00"),
    )

    trial_balance = generate_trial_balance(ledger_book)

    assert trial_balance.account_count == 0
    assert trial_balance.total_debit == Decimal("0.00")
    assert trial_balance.total_credit == Decimal("0.00")
    assert trial_balance.is_balanced is True


def test_trial_balance_rows_are_sorted_by_account():
    transactions = [
        make_transaction(
            "Sales",
            "50000",
            "Cash",
            "Sales",
        ),
        make_transaction(
            "Purchase",
            "30000",
            "Purchases",
            "Cash",
        ),
    ]

    journals = [
        generate_journal(transaction)
        for transaction in transactions
    ]

    ledger_book = post_journals_to_ledger(journals)

    trial_balance = generate_trial_balance(ledger_book)

    accounts = [
        row.account
        for row in trial_balance.rows
    ]

    assert accounts == sorted(accounts)


def test_missing_trial_balance_account_returns_none():
    transaction = make_transaction(
        "Purchase",
        "30000",
        "Purchases",
        "Cash",
    )

    journal = generate_journal(transaction)

    ledger_book = post_journals_to_ledger([journal])

    trial_balance = generate_trial_balance(ledger_book)

    assert (
        get_trial_balance_row(
            trial_balance,
            "Bank",
        )
        is None
    )