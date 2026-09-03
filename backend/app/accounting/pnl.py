from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.accounting.trading import TradingAccount


ZERO = Decimal("0.00")


class ProfitLossError(ValueError):
    """Raised when Profit & Loss data is invalid."""


@dataclass(frozen=True)
class ProfitLoss:
    """
    Represents the Profit & Loss Account.

    Gross Profit/Gross Loss is transferred from the Trading Account.
    Indirect incomes are added to gross profit, while indirect expenses
    are deducted to determine the final net profit or net loss.
    """

    gross_profit: Decimal = ZERO
    gross_loss: Decimal = ZERO
    indirect_incomes: Decimal = ZERO
    indirect_expenses: Decimal = ZERO

    @property
    def total_income(self) -> Decimal:
        """Gross profit plus indirect incomes."""
        return self.gross_profit + self.indirect_incomes

    @property
    def total_expenses(self) -> Decimal:
        """Gross loss plus indirect expenses."""
        return self.gross_loss + self.indirect_expenses

    @property
    def net_profit(self) -> Decimal:
        """Return net profit when total income exceeds total expenses."""
        return max(
            self.total_income - self.total_expenses,
            ZERO,
        )

    @property
    def net_loss(self) -> Decimal:
        """Return net loss when total expenses exceed total income."""
        return max(
            self.total_expenses - self.total_income,
            ZERO,
        )

    @property
    def is_profit(self) -> bool:
        """Return True when the result is a net profit."""
        return self.net_profit > ZERO

    @property
    def is_loss(self) -> bool:
        """Return True when the result is a net loss."""
        return self.net_loss > ZERO

    @property
    def is_balanced(self) -> bool:
        """
        Verify the P&L balancing equation.

        Total Income + Net Loss
        =
        Total Expenses + Net Profit
        """
        left_side = self.total_income + self.net_loss
        right_side = self.total_expenses + self.net_profit

        return left_side == right_side

    def validate(self) -> None:
        """Validate all P&L amounts."""

        amounts = {
            "gross_profit": self.gross_profit,
            "gross_loss": self.gross_loss,
            "indirect_incomes": self.indirect_incomes,
            "indirect_expenses": self.indirect_expenses,
        }

        for name, amount in amounts.items():
            if not isinstance(amount, Decimal):
                raise ProfitLossError(
                    f"{name} must be a Decimal value."
                )

            if not amount.is_finite():
                raise ProfitLossError(
                    f"{name} must be a finite amount."
                )

            if amount < ZERO:
                raise ProfitLossError(
                    f"{name} cannot be negative."
                )

        if self.gross_profit > ZERO and self.gross_loss > ZERO:
            raise ProfitLossError(
                "Gross profit and gross loss cannot both be present."
            )

    def calculate(self) -> "ProfitLoss":
        """Validate and return the calculated P&L."""
        self.validate()

        if not self.is_balanced:
            raise ProfitLossError(
                "Profit & Loss Account is not balanced."
            )

        return self


def _to_decimal(
    value: Decimal | int | float | str,
) -> Decimal:
    """Convert a supported numeric value to a two-decimal Decimal."""

    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise ProfitLossError(
            f"Invalid monetary value: {value!r}."
        ) from exc

    if not amount.is_finite():
        raise ProfitLossError(
            f"Amount must be finite: {value!r}."
        )

    if amount < ZERO:
        raise ProfitLossError(
            f"Amount cannot be negative: {value!r}."
        )

    return amount.quantize(Decimal("0.01"))


def generate_pnl(
    *,
    gross_profit: Decimal | int | float | str = ZERO,
    gross_loss: Decimal | int | float | str = ZERO,
    indirect_incomes: Decimal | int | float | str = ZERO,
    indirect_expenses: Decimal | int | float | str = ZERO,
) -> ProfitLoss:
    """
    Generate a validated Profit & Loss Account.

    Parameters
    ----------
    gross_profit:
        Gross profit transferred from the Trading Account.

    gross_loss:
        Gross loss transferred from the Trading Account.

    indirect_incomes:
        Income not directly related to trading activity.

    indirect_expenses:
        Expenses not directly related to trading activity.
    """

    pnl = ProfitLoss(
        gross_profit=_to_decimal(gross_profit),
        gross_loss=_to_decimal(gross_loss),
        indirect_incomes=_to_decimal(indirect_incomes),
        indirect_expenses=_to_decimal(indirect_expenses),
    )

    pnl.validate()

    return pnl


def generate_pnl_from_trading(
    trading_account: TradingAccount,
    *,
    indirect_incomes: Decimal | int | float | str = ZERO,
    indirect_expenses: Decimal | int | float | str = ZERO,
) -> ProfitLoss:
    """
    Generate P&L directly from a Trading Account.

    Gross profit or gross loss is automatically transferred from
    the Trading Account.
    """

    trading_account.validate()

    return generate_pnl(
        gross_profit=trading_account.gross_profit,
        gross_loss=trading_account.gross_loss,
        indirect_incomes=indirect_incomes,
        indirect_expenses=indirect_expenses,
    )


def get_net_profit(pnl: ProfitLoss) -> Decimal:
    """Return net profit."""
    pnl.validate()
    return pnl.net_profit


def get_net_loss(pnl: ProfitLoss) -> Decimal:
    """Return net loss."""
    pnl.validate()
    return pnl.net_loss


def get_total_income(pnl: ProfitLoss) -> Decimal:
    """Return total income."""
    pnl.validate()
    return pnl.total_income


def get_total_expenses(pnl: ProfitLoss) -> Decimal:
    """Return total expenses."""
    pnl.validate()
    return pnl.total_expenses