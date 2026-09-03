from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class LedgerLine:
    """
    One journal posting inside an account ledger.
    """

    date: object
    description: str
    debit: Decimal
    credit: Decimal

    @property
    def amount(self) -> Decimal:
        return self.debit if self.debit > ZERO else self.credit


@dataclass
class AccountLedger:
    """
    Ledger for a single accounting account.
    """

    account: str
    lines: list[LedgerLine] = field(default_factory=list)

    @property
    def total_debit(self) -> Decimal:
        return sum(
            (line.debit for line in self.lines),
            ZERO,
        )

    @property
    def total_credit(self) -> Decimal:
        return sum(
            (line.credit for line in self.lines),
            ZERO,
        )

    @property
    def balance(self) -> Decimal:
        """
        Net ledger balance.

        Positive  -> Debit balance
        Negative  -> Credit balance
        Zero      -> Balanced
        """
        return self.total_debit - self.total_credit

    @property
    def debit_balance(self) -> Decimal:
        return max(self.balance, ZERO)

    @property
    def credit_balance(self) -> Decimal:
        return max(-self.balance, ZERO)

    @property
    def balance_type(self) -> str:
        if self.balance > ZERO:
            return "DEBIT"

        if self.balance < ZERO:
            return "CREDIT"

        return "BALANCED"

    def add_line(
        self,
        *,
        date: object,
        description: str,
        debit: Decimal = ZERO,
        credit: Decimal = ZERO,
    ) -> None:
        """
        Add a validated journal posting to this ledger.
        """

        if debit < ZERO:
            raise ValueError("Debit amount cannot be negative.")

        if credit < ZERO:
            raise ValueError("Credit amount cannot be negative.")

        if debit > ZERO and credit > ZERO:
            raise ValueError(
                "A ledger line cannot contain both debit and credit."
            )

        if debit == ZERO and credit == ZERO:
            raise ValueError(
                "A ledger line must contain either debit or credit."
            )

        self.lines.append(
            LedgerLine(
                date=date,
                description=description,
                debit=debit,
                credit=credit,
            )
        )


@dataclass
class LedgerBook:
    """
    Collection of account-wise ledgers.
    """

    accounts: dict[str, AccountLedger] = field(default_factory=dict)

    def get_or_create(self, account: str) -> AccountLedger:
        """
        Get an existing account ledger or create a new one.
        """

        account = account.strip()

        if not account:
            raise ValueError("Account name cannot be empty.")

        if account not in self.accounts:
            self.accounts[account] = AccountLedger(
                account=account
            )

        return self.accounts[account]

    @property
    def total_debit(self) -> Decimal:
        return sum(
            (ledger.total_debit for ledger in self.accounts.values()),
            ZERO,
        )

    @property
    def total_credit(self) -> Decimal:
        return sum(
            (ledger.total_credit for ledger in self.accounts.values()),
            ZERO,
        )

    def get_account(self, account: str) -> AccountLedger | None:
        return self.accounts.get(account.strip())

    def account_names(self) -> list[str]:
        return sorted(self.accounts.keys())


def post_journal_to_ledger(
    ledger_book: LedgerBook,
    journal_entry,
) -> LedgerBook:
    """
    Post one validated JournalEntryData into the ledger.

    Every journal line is posted to the corresponding account.
    """

    if not journal_entry.is_balanced:
        raise ValueError(
            "Cannot post an unbalanced journal entry."
        )

    for line in journal_entry.lines:
        account_ledger = ledger_book.get_or_create(line.account)

        account_ledger.add_line(
            date=journal_entry.entry_date,
            description=journal_entry.description,
            debit=line.debit,
            credit=line.credit,
        )

    return ledger_book


def post_journals_to_ledger(
    journal_entries: Iterable,
) -> LedgerBook:
    """
    Build a complete ledger from multiple journal entries.
    """

    ledger_book = LedgerBook()

    for journal_entry in journal_entries:
        post_journal_to_ledger(
            ledger_book,
            journal_entry,
        )

    return ledger_book


def get_account_balance(
    ledger_book: LedgerBook,
    account: str,
) -> Decimal:
    """
    Return the signed balance of an account.

    Positive = Debit
    Negative = Credit
    Zero = Balanced / no activity
    """

    ledger = ledger_book.get_account(account)

    if ledger is None:
        return ZERO

    return ledger.balance


def get_trial_balance_totals(
    ledger_book: LedgerBook,
) -> tuple[Decimal, Decimal]:
    """
    Calculate debit and credit totals from ledger balances.

    This helper will also be used by the Trial Balance engine.
    """

    debit_total = sum(
        (
            ledger.debit_balance
            for ledger in ledger_book.accounts.values()
        ),
        ZERO,
    )

    credit_total = sum(
        (
            ledger.credit_balance
            for ledger in ledger_book.accounts.values()
        ),
        ZERO,
    )

    return debit_total, credit_total