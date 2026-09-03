from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.accounting.balance_sheet import BalanceSheet, BalanceSheetItem
from app.accounting.journal import JournalEntryData, JournalLineData
from app.accounting.ledger import LedgerBook, post_journals_to_ledger
from app.accounting.pnl import ProfitLoss
from app.accounting.reconciliation import (
    ReconciliationCheck,
    ReconciliationError,
    ReconciliationReport,
    assert_reconciled,
    reconcile_all,
    reconcile_balance_sheet,
    reconcile_journal_to_ledger,
    reconcile_journals,
    reconcile_ledger,
    reconcile_ledger_to_trial_balance,
    reconcile_profit_loss,
    reconcile_trading_account,
    reconcile_trial_balance,
)
from app.accounting.trading import TradingAccount
from app.accounting.trial_balance import TrialBalance, TrialBalanceRow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_journal_entry(
    *,
    amount: Decimal = Decimal("100.00"),
    debit_account: str = "Cash",
    credit_account: str = "Sales",
    entry_date: date = date(2026, 1, 1),
    description: str = "Test transaction",
) -> JournalEntryData:
    return JournalEntryData(
        transaction_id=uuid4(),
        entry_date=entry_date,
        description=description,
        lines=(
            JournalLineData(
                account=debit_account,
                debit=amount,
                credit=Decimal("0.00"),
                description=description,
            ),
            JournalLineData(
                account=credit_account,
                debit=Decimal("0.00"),
                credit=amount,
                description=description,
            ),
        ),
    )


def make_ledger(
    entries: list[JournalEntryData],
) -> LedgerBook:
    return post_journals_to_ledger(entries)


def make_balanced_trial_balance() -> TrialBalance:
    return TrialBalance(
        rows=(
            TrialBalanceRow(
                account="Cash",
                debit=Decimal("100.00"),
                credit=Decimal("0.00"),
            ),
            TrialBalanceRow(
                account="Sales",
                debit=Decimal("0.00"),
                credit=Decimal("100.00"),
            ),
        )
    )


def make_balanced_trading_account() -> TradingAccount:
    return TradingAccount(
        opening_stock=Decimal("0.00"),
        purchases=Decimal("100.00"),
        purchase_returns=Decimal("0.00"),
        direct_expenses=Decimal("0.00"),
        sales=Decimal("150.00"),
        sales_returns=Decimal("0.00"),
        closing_stock=Decimal("0.00"),
    )


def make_balanced_profit_loss() -> ProfitLoss:
    return ProfitLoss(
        gross_profit=Decimal("50.00"),
        gross_loss=Decimal("0.00"),
        indirect_incomes=Decimal("0.00"),
        indirect_expenses=Decimal("0.00"),
    )


def make_balanced_balance_sheet() -> BalanceSheet:
    return BalanceSheet(
        current_assets=(
            BalanceSheetItem(
                account="Cash",
                amount=Decimal("100.00"),
            ),
        ),
        liabilities=(),
        capital=Decimal("100.00"),
    )


# ---------------------------------------------------------------------------
# ReconciliationCheck
# ---------------------------------------------------------------------------

def test_reconciliation_check_passes_when_values_match():
    check = ReconciliationCheck.create(
        name="Test Check",
        expected=Decimal("100.00"),
        actual=Decimal("100.00"),
    )

    assert check.passed is True
    assert check.difference == Decimal("0.00")
    assert check.name == "Test Check"


def test_reconciliation_check_fails_when_values_differ():
    check = ReconciliationCheck.create(
        name="Test Check",
        expected=Decimal("100.00"),
        actual=Decimal("90.00"),
    )

    assert check.passed is False
    assert check.difference == Decimal("-10.00")
    assert "failed" in check.message.lower()


def test_reconciliation_check_custom_message():
    check = ReconciliationCheck.create(
        name="Test Check",
        expected=Decimal("100.00"),
        actual=Decimal("90.00"),
        message="Custom failure message",
    )

    assert check.message == "Custom failure message"


# ---------------------------------------------------------------------------
# ReconciliationReport
# ---------------------------------------------------------------------------

def test_reconciliation_report_properties():
    passed = ReconciliationCheck.create(
        name="Passed",
        expected=Decimal("100.00"),
        actual=Decimal("100.00"),
    )

    failed = ReconciliationCheck.create(
        name="Failed",
        expected=Decimal("100.00"),
        actual=Decimal("90.00"),
    )

    report = ReconciliationReport(
        checks=(passed, failed),
    )

    assert report.total_checks == 2
    assert report.passed_checks == 1
    assert report.failed_checks == 1
    assert report.is_reconciled is False
    assert report.status == "NOT_RECONCILED"
    assert len(report.failures) == 1


def test_empty_reconciliation_report_is_reconciled():
    report = ReconciliationReport(checks=())

    assert report.total_checks == 0
    assert report.passed_checks == 0
    assert report.failed_checks == 0
    assert report.is_reconciled is True
    assert report.status == "RECONCILED"
    assert report.failures == ()


# ---------------------------------------------------------------------------
# Journal reconciliation
# ---------------------------------------------------------------------------

def test_reconcile_empty_journals():
    check = reconcile_journals([])

    assert check.passed is True
    assert check.difference == Decimal("0.00")


def test_reconcile_balanced_journals():
    entries = [
        make_journal_entry(amount=Decimal("100.00")),
        make_journal_entry(amount=Decimal("250.00")),
    ]

    check = reconcile_journals(entries)

    assert check.passed is True
    assert check.expected == Decimal("350.00")
    assert check.actual == Decimal("350.00")
    assert check.difference == Decimal("0.00")


def test_reconcile_unbalanced_journal():
    entry = JournalEntryData(
        transaction_id=uuid4(),
        entry_date=date(2026, 1, 1),
        description="Unbalanced transaction",
        lines=(
            JournalLineData(
                account="Cash",
                debit=Decimal("100.00"),
                credit=Decimal("0.00"),
                description="Unbalanced transaction",
            ),
            JournalLineData(
                account="Sales",
                debit=Decimal("0.00"),
                credit=Decimal("90.00"),
                description="Unbalanced transaction",
            ),
        ),
    )

    check = reconcile_journals([entry])

    assert check.passed is False
    assert check.expected == Decimal("100.00")
    assert check.actual == Decimal("90.00")


# ---------------------------------------------------------------------------
# Ledger reconciliation
# ---------------------------------------------------------------------------

def test_reconcile_empty_ledger():
    ledger = LedgerBook()

    check = reconcile_ledger(ledger)

    assert check.passed is True
    assert check.difference == Decimal("0.00")


def test_reconcile_balanced_ledger():
    entries = [make_journal_entry(amount=Decimal("100.00"))]
    ledger = make_ledger(entries)

    check = reconcile_ledger(ledger)

    assert check.passed is True
    assert check.expected == Decimal("100.00")
    assert check.actual == Decimal("100.00")


# ---------------------------------------------------------------------------
# Trial balance reconciliation
# ---------------------------------------------------------------------------

def test_reconcile_balanced_trial_balance():
    trial_balance = make_balanced_trial_balance()

    check = reconcile_trial_balance(trial_balance)

    assert check.passed is True
    assert check.expected == Decimal("100.00")
    assert check.actual == Decimal("100.00")


def test_reconcile_empty_trial_balance():
    trial_balance = TrialBalance(rows=())

    check = reconcile_trial_balance(trial_balance)

    assert check.passed is True
    assert check.difference == Decimal("0.00")


# ---------------------------------------------------------------------------
# Journal -> Ledger reconciliation
# ---------------------------------------------------------------------------

def test_reconcile_journal_to_ledger():
    entries = [
        make_journal_entry(amount=Decimal("100.00")),
        make_journal_entry(amount=Decimal("50.00")),
    ]

    ledger = make_ledger(entries)

    check = reconcile_journal_to_ledger(entries, ledger)

    assert check.passed is True
    assert check.difference == Decimal("0.00")


# ---------------------------------------------------------------------------
# Ledger -> Trial Balance reconciliation
# ---------------------------------------------------------------------------

def test_reconcile_ledger_to_trial_balance():
    entries = [make_journal_entry(amount=Decimal("100.00"))]
    ledger = make_ledger(entries)
    trial_balance = make_balanced_trial_balance()

    check = reconcile_ledger_to_trial_balance(
        ledger,
        trial_balance,
    )

    assert check.passed is True
    assert check.difference == Decimal("0.00")


# ---------------------------------------------------------------------------
# Trading Account
# ---------------------------------------------------------------------------

def test_reconcile_trading_account():
    trading = make_balanced_trading_account()

    check = reconcile_trading_account(trading)

    assert check.passed is True
    assert check.difference == Decimal("0.00")


def test_reconcile_trading_account_with_gross_profit():
    trading = TradingAccount(
        opening_stock=Decimal("0.00"),
        purchases=Decimal("100.00"),
        purchase_returns=Decimal("0.00"),
        direct_expenses=Decimal("0.00"),
        sales=Decimal("150.00"),
        sales_returns=Decimal("0.00"),
        closing_stock=Decimal("0.00"),
    )

    check = reconcile_trading_account(trading)

    assert check.passed is True


# ---------------------------------------------------------------------------
# Profit & Loss
# ---------------------------------------------------------------------------

def test_reconcile_profit_loss():
    pnl = make_balanced_profit_loss()

    check = reconcile_profit_loss(pnl)

    assert check.passed is True
    assert check.difference == Decimal("0.00")


def test_reconcile_profit_loss_with_expenses():
    pnl = ProfitLoss(
        gross_profit=Decimal("100.00"),
        gross_loss=Decimal("0.00"),
        indirect_incomes=Decimal("20.00"),
        indirect_expenses=Decimal("30.00"),
    )

    check = reconcile_profit_loss(pnl)

    assert check.passed is True


# ---------------------------------------------------------------------------
# Balance Sheet
# ---------------------------------------------------------------------------

def test_reconcile_balance_sheet():
    balance_sheet = make_balanced_balance_sheet()

    check = reconcile_balance_sheet(balance_sheet)

    assert check.passed is True
    assert check.difference == Decimal("0.00")


# ---------------------------------------------------------------------------
# reconcile_all
# ---------------------------------------------------------------------------

def test_reconcile_all_with_empty_inputs():
    report = reconcile_all()

    assert isinstance(report, ReconciliationReport)
    assert report.is_reconciled is True
    assert report.failed_checks == 0


def test_reconcile_all_with_journal_ledger_and_trial_balance():
    entries = [make_journal_entry(amount=Decimal("100.00"))]
    ledger = make_ledger(entries)
    trial_balance = make_balanced_trial_balance()

    report = reconcile_all(
        journal_entries=entries,
        ledger_book=ledger,
        trial_balance=trial_balance,
    )

    assert isinstance(report, ReconciliationReport)
    assert report.total_checks >= 3
    assert report.failed_checks == 0
    assert report.is_reconciled is True


# ---------------------------------------------------------------------------
# assert_reconciled
# ---------------------------------------------------------------------------

def test_assert_reconciled_does_not_raise_for_valid_report():
    report = ReconciliationReport(
        checks=(
            ReconciliationCheck.create(
                name="Valid",
                expected=Decimal("100.00"),
                actual=Decimal("100.00"),
            ),
        )
    )

    assert_reconciled(report)


def test_assert_reconciled_raises_for_failed_report():
    report = ReconciliationReport(
        checks=(
            ReconciliationCheck.create(
                name="Invalid",
                expected=Decimal("100.00"),
                actual=Decimal("90.00"),
            ),
        )
    )

    with pytest.raises(ReconciliationError):
        assert_reconciled(report)


def test_failure_message_contains_check_name():
    report = ReconciliationReport(
        checks=(
            ReconciliationCheck.create(
                name="Important Check",
                expected=Decimal("100.00"),
                actual=Decimal("90.00"),
            ),
        )
    )

    with pytest.raises(ReconciliationError) as exc_info:
        assert_reconciled(report)

    assert "Important Check" in str(exc_info.value)