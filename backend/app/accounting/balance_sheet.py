from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable


ZERO = Decimal("0.00")


class BalanceSheetError(ValueError):
    """Raised when Balance Sheet data is invalid."""


@dataclass(frozen=True)
class BalanceSheetItem:
    """Represents one item on the Balance Sheet."""

    account: str
    amount: Decimal


@dataclass(frozen=True)
class BalanceSheet:
    """
    Represents the Balance Sheet of a business.

    Accounting equation:

        Assets = Liabilities + Equity

    Net profit increases equity.
    Net loss decreases equity.
    """

    fixed_assets: tuple[BalanceSheetItem, ...] = field(default_factory=tuple)
    current_assets: tuple[BalanceSheetItem, ...] = field(default_factory=tuple)
    liabilities: tuple[BalanceSheetItem, ...] = field(default_factory=tuple)
    capital: Decimal = ZERO
    drawings: Decimal = ZERO
    net_profit: Decimal = ZERO
    net_loss: Decimal = ZERO

    @property
    def total_fixed_assets(self) -> Decimal:
        """Total fixed assets."""
        return sum(
            (item.amount for item in self.fixed_assets),
            ZERO,
        )

    @property
    def total_current_assets(self) -> Decimal:
        """Total current assets."""
        return sum(
            (item.amount for item in self.current_assets),
            ZERO,
        )

    @property
    def total_assets(self) -> Decimal:
        """Total assets."""
        return self.total_fixed_assets + self.total_current_assets

    @property
    def total_liabilities(self) -> Decimal:
        """Total liabilities."""
        return sum(
            (item.amount for item in self.liabilities),
            ZERO,
        )

    @property
    def adjusted_capital(self) -> Decimal:
        """
        Calculate closing capital.

        Closing Capital =
            Opening Capital
            + Net Profit
            - Net Loss
            - Drawings
        """
        return (
            self.capital
            + self.net_profit
            - self.net_loss
            - self.drawings
        )

    @property
    def total_equity(self) -> Decimal:
        """Total equity after profit/loss and drawings."""
        return self.adjusted_capital

    @property
    def liabilities_and_equity(self) -> Decimal:
        """Total liabilities plus equity."""
        return self.total_liabilities + self.total_equity

    @property
    def difference(self) -> Decimal:
        """
        Difference between assets and liabilities + equity.

        A valid Balance Sheet must have difference = 0.
        """
        return self.total_assets - self.liabilities_and_equity

    @property
    def is_balanced(self) -> bool:
        """Return True when the accounting equation balances."""
        return self.difference == ZERO

    def validate(self) -> None:
        """Validate all Balance Sheet data."""

        self._validate_items(
            self.fixed_assets,
            "fixed_assets",
        )

        self._validate_items(
            self.current_assets,
            "current_assets",
        )

        self._validate_items(
            self.liabilities,
            "liabilities",
        )

        amounts = {
            "capital": self.capital,
            "drawings": self.drawings,
            "net_profit": self.net_profit,
            "net_loss": self.net_loss,
        }

        for name, amount in amounts.items():
            self._validate_amount(name, amount)

        if self.net_profit > ZERO and self.net_loss > ZERO:
            raise BalanceSheetError(
                "Net profit and net loss cannot both be present."
            )

        if self.drawings > self.capital + self.net_profit:
            raise BalanceSheetError(
                "Drawings cannot exceed available capital and profit."
            )

    @staticmethod
    def _validate_amount(
        name: str,
        amount: Decimal,
    ) -> None:
        """Validate a single monetary amount."""

        if not isinstance(amount, Decimal):
            raise BalanceSheetError(
                f"{name} must be a Decimal value."
            )

        if not amount.is_finite():
            raise BalanceSheetError(
                f"{name} must be a finite amount."
            )

        if amount < ZERO:
            raise BalanceSheetError(
                f"{name} cannot be negative."
            )

    @classmethod
    def _validate_items(
        cls,
        items: Iterable[BalanceSheetItem],
        field_name: str,
    ) -> None:
        """Validate Balance Sheet items."""

        for item in items:
            if not isinstance(item, BalanceSheetItem):
                raise BalanceSheetError(
                    f"All items in {field_name} must be BalanceSheetItem objects."
                )

            if not item.account.strip():
                raise BalanceSheetError(
                    f"Account name in {field_name} cannot be empty."
                )

            cls._validate_amount(
                f"{field_name}.{item.account}",
                item.amount,
            )

    def calculate(self) -> "BalanceSheet":
        """Validate and return the calculated Balance Sheet."""

        self.validate()

        if not self.is_balanced:
            raise BalanceSheetError(
                "Balance Sheet is not balanced: "
                f"Assets={self.total_assets}, "
                f"Liabilities + Equity={self.liabilities_and_equity}, "
                f"Difference={self.difference}."
            )

        return self


def _to_decimal(
    value: Decimal | int | float | str,
) -> Decimal:
    """Convert a supported numeric value into a two-decimal Decimal."""

    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise BalanceSheetError(
            f"Invalid monetary value: {value!r}."
        ) from exc

    if not amount.is_finite():
        raise BalanceSheetError(
            f"Amount must be finite: {value!r}."
        )

    if amount < ZERO:
        raise BalanceSheetError(
            f"Amount cannot be negative: {value!r}."
        )

    return amount.quantize(Decimal("0.01"))


def _create_items(
    items: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ],
) -> tuple[BalanceSheetItem, ...]:
    """Normalize Balance Sheet item input."""

    result: list[BalanceSheetItem] = []

    for item in items:
        if isinstance(item, BalanceSheetItem):
            result.append(
                BalanceSheetItem(
                    account=item.account.strip(),
                    amount=_to_decimal(item.amount),
                )
            )
            continue

        if isinstance(item, (tuple, list)) and len(item) == 2:
            account, amount = item

            account = str(account).strip()

            if not account:
                raise BalanceSheetError(
                    "Account name cannot be empty."
                )

            result.append(
                BalanceSheetItem(
                    account=account,
                    amount=_to_decimal(amount),
                )
            )
            continue

        raise BalanceSheetError(
            "Balance Sheet item must be a BalanceSheetItem "
            "or an (account, amount) pair."
        )

    return tuple(result)


def generate_balance_sheet(
    *,
    fixed_assets: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ] = (),
    current_assets: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ] = (),
    liabilities: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ] = (),
    capital: Decimal | int | float | str = ZERO,
    drawings: Decimal | int | float | str = ZERO,
    net_profit: Decimal | int | float | str = ZERO,
    net_loss: Decimal | int | float | str = ZERO,
) -> BalanceSheet:
    """
    Generate a validated Balance Sheet.

    Parameters
    ----------
    fixed_assets:
        Long-term assets such as machinery, furniture, buildings, etc.

    current_assets:
        Current assets such as cash, bank, inventory, debtors, etc.

    liabilities:
        Liabilities such as creditors, loans, outstanding expenses, etc.

    capital:
        Opening/introduced capital.

    drawings:
        Amount withdrawn by the owner.

    net_profit:
        Profit transferred from the P&L Account.

    net_loss:
        Loss transferred from the P&L Account.
    """

    balance_sheet = BalanceSheet(
        fixed_assets=_create_items(fixed_assets),
        current_assets=_create_items(current_assets),
        liabilities=_create_items(liabilities),
        capital=_to_decimal(capital),
        drawings=_to_decimal(drawings),
        net_profit=_to_decimal(net_profit),
        net_loss=_to_decimal(net_loss),
    )

    balance_sheet.validate()

    return balance_sheet


def generate_balance_sheet_from_pnl(
    pnl,
    *,
    fixed_assets: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ] = (),
    current_assets: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ] = (),
    liabilities: Iterable[
        BalanceSheetItem
        | tuple[str, Decimal | int | float | str]
    ] = (),
    capital: Decimal | int | float | str = ZERO,
    drawings: Decimal | int | float | str = ZERO,
) -> BalanceSheet:
    """
    Generate a Balance Sheet using the result of the P&L engine.

    Net profit is transferred when P&L produces profit.
    Net loss is transferred when P&L produces loss.
    """

    pnl.validate()

    return generate_balance_sheet(
        fixed_assets=fixed_assets,
        current_assets=current_assets,
        liabilities=liabilities,
        capital=capital,
        drawings=drawings,
        net_profit=pnl.net_profit,
        net_loss=pnl.net_loss,
    )


def get_total_assets(
    balance_sheet: BalanceSheet,
) -> Decimal:
    """Return total assets."""
    balance_sheet.validate()
    return balance_sheet.total_assets


def get_total_liabilities(
    balance_sheet: BalanceSheet,
) -> Decimal:
    """Return total liabilities."""
    balance_sheet.validate()
    return balance_sheet.total_liabilities


def get_adjusted_capital(
    balance_sheet: BalanceSheet,
) -> Decimal:
    """Return closing/adjusted capital."""
    balance_sheet.validate()
    return balance_sheet.adjusted_capital


def get_total_equity(
    balance_sheet: BalanceSheet,
) -> Decimal:
    """Return total equity."""
    balance_sheet.validate()
    return balance_sheet.total_equity


def get_balance_sheet_difference(
    balance_sheet: BalanceSheet,
) -> Decimal:
    """Return the Balance Sheet difference."""
    balance_sheet.validate()
    return balance_sheet.difference