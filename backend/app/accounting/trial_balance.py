from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.accounting.ledger import LedgerBook


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class TrialBalanceRow:
    """
    One account's position in the trial balance.
    """

    account: str
    debit: Decimal
    credit: Decimal

    @property
    def balance(self) -> Decimal:
        return self.debit - self.credit


@dataclass(frozen=True)
class TrialBalance:
    """
    Complete trial balance generated from the ledger.
    """

    rows: tuple[TrialBalanceRow, ...]

    @property
    def total_debit(self) -> Decimal:
        return sum(
            (row.debit for row in self.rows),
            ZERO,
        )

    @property
    def total_credit(self) -> Decimal:
        return sum(
            (row.credit for row in self.rows),
            ZERO,
        )

    @property
    def difference(self) -> Decimal:
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return self.difference == ZERO

    @property
    def account_count(self) -> int:
        return len(self.rows)


def generate_trial_balance(
    ledger_book: LedgerBook,
) -> TrialBalance:
    """
    Generate a trial balance from the closing balances
    of all ledger accounts.

    Debit balance  -> Trial Balance debit column
    Credit balance -> Trial Balance credit column
    Zero balance   -> omitted
    """

    rows: list[TrialBalanceRow] = []

    for account_name in ledger_book.account_names():
        ledger = ledger_book.get_account(account_name)

        if ledger is None:
            continue

        if ledger.debit_balance > ZERO:
            rows.append(
                TrialBalanceRow(
                    account=account_name,
                    debit=ledger.debit_balance,
                    credit=ZERO,
                )
            )

        elif ledger.credit_balance > ZERO:
            rows.append(
                TrialBalanceRow(
                    account=account_name,
                    debit=ZERO,
                    credit=ledger.credit_balance,
                )
            )

    trial_balance = TrialBalance(
        rows=tuple(rows),
    )

    if not trial_balance.is_balanced:
        raise ValueError(
            "Trial balance is not balanced: "
            f"Debit={trial_balance.total_debit}, "
            f"Credit={trial_balance.total_credit}."
        )

    return trial_balance


def get_trial_balance_row(
    trial_balance: TrialBalance,
    account: str,
) -> TrialBalanceRow | None:
    """
    Retrieve a specific account from the trial balance.
    """

    account = account.strip()

    for row in trial_balance.rows:
        if row.account == account:
            return row

    return None