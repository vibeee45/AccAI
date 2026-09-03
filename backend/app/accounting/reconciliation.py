from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.accounting.balance_sheet import BalanceSheet
from app.accounting.journal import JournalEntryData
from app.accounting.ledger import LedgerBook
from app.accounting.pnl import ProfitLoss
from app.accounting.trading import TradingAccount
from app.accounting.trial_balance import TrialBalance


ZERO = Decimal("0.00")


class ReconciliationError(ValueError):
    """Raised when reconciliation data is invalid."""


@dataclass(frozen=True)
class ReconciliationCheck:
    """
    Represents the result of one reconciliation check.
    """

    name: str
    expected: Decimal
    actual: Decimal
    difference: Decimal
    passed: bool
    message: str

    @classmethod
    def create(
        cls,
        *,
        name: str,
        expected: Decimal,
        actual: Decimal,
        message: str | None = None,
    ) -> "ReconciliationCheck":
        difference = actual - expected

        passed = difference == ZERO

        if message is None:
            message = (
                f"{name} passed."
                if passed
                else (
                    f"{name} failed: "
                    f"expected={expected}, actual={actual}, "
                    f"difference={difference}."
                )
            )

        return cls(
            name=name,
            expected=expected,
            actual=actual,
            difference=difference,
            passed=passed,
            message=message,
        )


@dataclass(frozen=True)
class ReconciliationReport:
    """
    Complete reconciliation report for an accounting period.
    """

    checks: tuple[ReconciliationCheck, ...]

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(
            1 for check in self.checks if check.passed
        )

    @property
    def failed_checks(self) -> int:
        return sum(
            1 for check in self.checks if not check.passed
        )

    @property
    def is_reconciled(self) -> bool:
        return all(
            check.passed
            for check in self.checks
        )

    @property
    def status(self) -> str:
        return (
            "RECONCILED"
            if self.is_reconciled
            else "NOT_RECONCILED"
        )

    @property
    def failures(self) -> tuple[ReconciliationCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if not check.passed
        )


def _decimal(value: Decimal | int | float | str) -> Decimal:
    """
    Convert a value to a two-decimal Decimal.
    """

    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise ReconciliationError(
            f"Invalid reconciliation amount: {value!r}."
        ) from exc

    if not amount.is_finite():
        raise ReconciliationError(
            f"Reconciliation amount must be finite: {value!r}."
        )

    return amount.quantize(Decimal("0.01"))


def reconcile_journals(
    journal_entries: Iterable[JournalEntryData],
) -> ReconciliationCheck:
    """
    Verify that all journal entries are balanced.

    Every journal entry must satisfy:

        Total Debit = Total Credit
    """

    entries = tuple(journal_entries)

    total_debit = ZERO
    total_credit = ZERO

    for journal in entries:
        if not journal.is_balanced:
            return ReconciliationCheck.create(
                name="Journal Balance",
                expected=journal.total_debit,
                actual=journal.total_credit,
                message=(
                    "Journal reconciliation failed because "
                    "at least one journal entry is unbalanced."
                ),
            )

        total_debit += journal.total_debit
        total_credit += journal.total_credit

    return ReconciliationCheck.create(
        name="Journal Balance",
        expected=total_debit,
        actual=total_credit,
        message=(
            "All journal entries are balanced."
            if total_debit == total_credit
            else None
        ),
    )


def reconcile_ledger(
    ledger_book: LedgerBook,
) -> ReconciliationCheck:
    """
    Verify that total ledger debits equal total ledger credits.
    """

    total_debit = ledger_book.total_debit
    total_credit = ledger_book.total_credit

    return ReconciliationCheck.create(
        name="Ledger Balance",
        expected=total_debit,
        actual=total_credit,
        message=(
            "Ledger is balanced."
            if total_debit == total_credit
            else None
        ),
    )


def reconcile_trial_balance(
    trial_balance: TrialBalance,
) -> ReconciliationCheck:
    """
    Verify that Trial Balance debit and credit totals agree.
    """

    total_debit = trial_balance.total_debit
    total_credit = trial_balance.total_credit

    return ReconciliationCheck.create(
        name="Trial Balance",
        expected=total_debit,
        actual=total_credit,
        message=(
            "Trial Balance is balanced."
            if total_debit == total_credit
            else None
        ),
    )


def reconcile_journal_to_ledger(
    journal_entries: Iterable[JournalEntryData],
    ledger_book: LedgerBook,
) -> ReconciliationCheck:
    """
    Verify that total journal amounts agree with total ledger amounts.
    """

    journal_entries = tuple(journal_entries)

    journal_debit = sum(
        (entry.total_debit for entry in journal_entries),
        ZERO,
    )

    journal_credit = sum(
        (entry.total_credit for entry in journal_entries),
        ZERO,
    )

    ledger_debit = ledger_book.total_debit
    ledger_credit = ledger_book.total_credit

    journal_total = journal_debit + journal_credit
    ledger_total = ledger_debit + ledger_credit

    return ReconciliationCheck.create(
        name="Journal to Ledger",
        expected=journal_total,
        actual=ledger_total,
        message=(
            "Journal and Ledger totals agree."
            if journal_total == ledger_total
            else (
                "Journal and Ledger totals do not agree: "
                f"journal={journal_total}, "
                f"ledger={ledger_total}."
            )
        ),
    )


def reconcile_ledger_to_trial_balance(
    ledger_book: LedgerBook,
    trial_balance: TrialBalance,
) -> ReconciliationCheck:
    """
    Verify that ledger balances agree with Trial Balance balances.

    Trial Balance contains the net debit/credit balance of each ledger.
    """

    ledger_debit, ledger_credit = (
        _ledger_trial_balance_totals(ledger_book)
    )

    trial_debit = trial_balance.total_debit
    trial_credit = trial_balance.total_credit

    expected = ledger_debit + ledger_credit
    actual = trial_debit + trial_credit

    return ReconciliationCheck.create(
        name="Ledger to Trial Balance",
        expected=expected,
        actual=actual,
        message=(
            "Ledger and Trial Balance balances agree."
            if expected == actual
            else (
                "Ledger and Trial Balance balances do not agree: "
                f"ledger={expected}, "
                f"trial_balance={actual}."
            )
        ),
    )


def _ledger_trial_balance_totals(
    ledger_book: LedgerBook,
) -> tuple[Decimal, Decimal]:
    """
    Calculate Trial Balance totals directly from ledger balances.
    """

    debit_total = ZERO
    credit_total = ZERO

    for ledger in ledger_book.accounts.values():
        debit_total += ledger.debit_balance
        credit_total += ledger.credit_balance

    return debit_total, credit_total


def reconcile_trading_account(
    trading_account: TradingAccount,
) -> ReconciliationCheck:
    """
    Verify the Trading Account balancing equation.
    """

    trading_account.validate()

    expected = (
        trading_account.net_sales
        + trading_account.gross_loss
    )

    actual = (
        trading_account.cost_of_goods_sold
        + trading_account.gross_profit
    )

    return ReconciliationCheck.create(
        name="Trading Account",
        expected=expected,
        actual=actual,
        message=(
            "Trading Account is balanced."
            if expected == actual
            else (
                "Trading Account is not balanced: "
                f"sales side={expected}, "
                f"cost side={actual}."
            )
        ),
    )


def reconcile_profit_loss(
    pnl: ProfitLoss,
) -> ReconciliationCheck:
    """
    Verify the Profit & Loss balancing equation.
    """

    pnl.validate()

    expected = (
        pnl.total_income
        + pnl.net_loss
    )

    actual = (
        pnl.total_expenses
        + pnl.net_profit
    )

    return ReconciliationCheck.create(
        name="Profit & Loss",
        expected=expected,
        actual=actual,
        message=(
            "Profit & Loss Account is balanced."
            if expected == actual
            else (
                "Profit & Loss Account is not balanced: "
                f"income side={expected}, "
                f"expense side={actual}."
            )
        ),
    )


def reconcile_balance_sheet(
    balance_sheet: BalanceSheet,
) -> ReconciliationCheck:
    """
    Verify the Balance Sheet accounting equation.

        Assets = Liabilities + Equity
    """

    balance_sheet.validate()

    assets = balance_sheet.total_assets
    liabilities_and_equity = (
        balance_sheet.liabilities_and_equity
    )

    return ReconciliationCheck.create(
        name="Balance Sheet",
        expected=assets,
        actual=liabilities_and_equity,
        message=(
            "Balance Sheet is balanced."
            if assets == liabilities_and_equity
            else (
                "Balance Sheet is not balanced: "
                f"assets={assets}, "
                f"liabilities_and_equity="
                f"{liabilities_and_equity}."
            )
        ),
    )


def reconcile_all(
    *,
    journal_entries: Iterable[JournalEntryData] | None = None,
    ledger_book: LedgerBook | None = None,
    trial_balance: TrialBalance | None = None,
    trading_account: TradingAccount | None = None,
    pnl: ProfitLoss | None = None,
    balance_sheet: BalanceSheet | None = None,
) -> ReconciliationReport:
    """
    Run all available reconciliation checks.

    Checks are only performed when the corresponding accounting
    object is supplied.

    This allows ACCAI to progressively reconcile an accounting
    pipeline without requiring every statement to be available.
    """

    checks: list[ReconciliationCheck] = []

    journal_entries_tuple: tuple[JournalEntryData, ...] | None = None

    if journal_entries is not None:
        journal_entries_tuple = tuple(journal_entries)

        checks.append(
            reconcile_journals(
                journal_entries_tuple
            )
        )

    if ledger_book is not None:
        checks.append(
            reconcile_ledger(ledger_book)
        )

    if trial_balance is not None:
        checks.append(
            reconcile_trial_balance(trial_balance)
        )

    if (
        journal_entries_tuple is not None
        and ledger_book is not None
    ):
        checks.append(
            reconcile_journal_to_ledger(
                journal_entries_tuple,
                ledger_book,
            )
        )

    if (
        ledger_book is not None
        and trial_balance is not None
    ):
        checks.append(
            reconcile_ledger_to_trial_balance(
                ledger_book,
                trial_balance,
            )
        )

    if trading_account is not None:
        checks.append(
            reconcile_trading_account(
                trading_account
            )
        )

    if pnl is not None:
        checks.append(
            reconcile_profit_loss(pnl)
        )

    if balance_sheet is not None:
        checks.append(
            reconcile_balance_sheet(
                balance_sheet
            )
        )

    return ReconciliationReport(
        checks=tuple(checks)
    )


def assert_reconciled(
    report: ReconciliationReport,
) -> None:
    """
    Raise an error if any reconciliation check failed.
    """

    if report.is_reconciled:
        return

    failed_messages = "; ".join(
        check.message
        for check in report.failures
    )

    raise ReconciliationError(
        "Accounting reconciliation failed: "
        f"{failed_messages}"
    )