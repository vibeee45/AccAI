from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


ZERO = Decimal("0.00")


class TradingAccountError(ValueError):
    """Raised when Trading Account data is invalid."""


@dataclass(frozen=True)
class TradingAccount:
    """
    Represents the Trading Account for a financial period.

    The Trading Account determines:
        - Cost of Goods Sold (COGS)
        - Gross Profit
        - Gross Loss
    """

    opening_stock: Decimal = ZERO
    purchases: Decimal = ZERO
    purchase_returns: Decimal = ZERO
    direct_expenses: Decimal = ZERO
    sales: Decimal = ZERO
    sales_returns: Decimal = ZERO
    closing_stock: Decimal = ZERO

    @property
    def net_purchases(self) -> Decimal:
        """Purchases after deducting purchase returns."""
        return self.purchases - self.purchase_returns

    @property
    def net_sales(self) -> Decimal:
        """Sales after deducting sales returns."""
        return self.sales - self.sales_returns

    @property
    def cost_of_goods_available(self) -> Decimal:
        """
        Opening Stock + Net Purchases + Direct Expenses.
        """
        return (
            self.opening_stock
            + self.net_purchases
            + self.direct_expenses
        )

    @property
    def cost_of_goods_sold(self) -> Decimal:
        """
        Cost of Goods Available - Closing Stock.
        """
        return self.cost_of_goods_available - self.closing_stock

    @property
    def gross_profit(self) -> Decimal:
        """
        Gross Profit when Net Sales exceed Cost of Goods Sold.

        Returns zero when the result is a gross loss.
        """
        return max(
            self.net_sales - self.cost_of_goods_sold,
            ZERO,
        )

    @property
    def gross_loss(self) -> Decimal:
        """
        Gross Loss when Cost of Goods Sold exceeds Net Sales.

        Returns zero when the result is a gross profit.
        """
        return max(
            self.cost_of_goods_sold - self.net_sales,
            ZERO,
        )

    @property
    def is_profit(self) -> bool:
        """Returns True when the Trading Account produces gross profit."""
        return self.gross_profit > ZERO

    @property
    def is_loss(self) -> bool:
        """Returns True when the Trading Account produces gross loss."""
        return self.gross_loss > ZERO

    @property
    def is_balanced(self) -> bool:
        """
        Trading Account balancing check.

        A Trading Account balances when:

            Net Sales + Gross Loss
            =
            COGS + Gross Profit
        """
        left_side = self.net_sales + self.gross_loss
        right_side = self.cost_of_goods_sold + self.gross_profit

        return left_side == right_side

    def validate(self) -> None:
        """Validate all Trading Account amounts."""
        amounts = {
            "opening_stock": self.opening_stock,
            "purchases": self.purchases,
            "purchase_returns": self.purchase_returns,
            "direct_expenses": self.direct_expenses,
            "sales": self.sales,
            "sales_returns": self.sales_returns,
            "closing_stock": self.closing_stock,
        }

        for name, amount in amounts.items():
            if not isinstance(amount, Decimal):
                raise TradingAccountError(
                    f"{name} must be a Decimal value."
                )

            if not amount.is_finite():
                raise TradingAccountError(
                    f"{name} must be a finite amount."
                )

            if amount < ZERO:
                raise TradingAccountError(
                    f"{name} cannot be negative."
                )

        if self.purchase_returns > self.purchases:
            raise TradingAccountError(
                "Purchase returns cannot exceed purchases."
            )

        if self.sales_returns > self.sales:
            raise TradingAccountError(
                "Sales returns cannot exceed sales."
            )

        if self.closing_stock > self.cost_of_goods_available:
            raise TradingAccountError(
                "Closing stock cannot exceed cost of goods available."
            )

    def calculate(self) -> "TradingAccount":
        """
        Validate and return the calculated Trading Account.

        The actual calculated values are exposed through properties.
        """
        self.validate()

        if not self.is_balanced:
            raise TradingAccountError(
                "Trading Account is not balanced."
            )

        return self


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    """
    Convert supported numeric input into a two-decimal Decimal.
    """
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise TradingAccountError(
            f"Invalid monetary value: {value!r}."
        ) from exc

    if not amount.is_finite():
        raise TradingAccountError(
            f"Amount must be finite: {value!r}."
        )

    if amount < ZERO:
        raise TradingAccountError(
            f"Amount cannot be negative: {value!r}."
        )

    return amount.quantize(Decimal("0.01"))


def generate_trading_account(
    *,
    opening_stock: Decimal | int | float | str = ZERO,
    purchases: Decimal | int | float | str = ZERO,
    purchase_returns: Decimal | int | float | str = ZERO,
    direct_expenses: Decimal | int | float | str = ZERO,
    sales: Decimal | int | float | str = ZERO,
    sales_returns: Decimal | int | float | str = ZERO,
    closing_stock: Decimal | int | float | str = ZERO,
) -> TradingAccount:
    """
    Create and validate a Trading Account.

    Parameters
    ----------
    opening_stock:
        Stock available at the beginning of the financial period.

    purchases:
        Total purchases during the period.

    purchase_returns:
        Goods returned to suppliers.

    direct_expenses:
        Expenses directly related to bringing goods to saleable condition,
        such as carriage inward, wages, customs duty, etc.

    sales:
        Total sales during the period.

    sales_returns:
        Goods returned by customers.

    closing_stock:
        Stock remaining at the end of the financial period.
    """

    trading_account = TradingAccount(
        opening_stock=_to_decimal(opening_stock),
        purchases=_to_decimal(purchases),
        purchase_returns=_to_decimal(purchase_returns),
        direct_expenses=_to_decimal(direct_expenses),
        sales=_to_decimal(sales),
        sales_returns=_to_decimal(sales_returns),
        closing_stock=_to_decimal(closing_stock),
    )

    trading_account.validate()

    return trading_account


def get_gross_profit(trading_account: TradingAccount) -> Decimal:
    """Return gross profit from a validated Trading Account."""
    trading_account.validate()
    return trading_account.gross_profit


def get_gross_loss(trading_account: TradingAccount) -> Decimal:
    """Return gross loss from a validated Trading Account."""
    trading_account.validate()
    return trading_account.gross_loss


def get_cost_of_goods_sold(
    trading_account: TradingAccount,
) -> Decimal:
    """Return Cost of Goods Sold from a validated Trading Account."""
    trading_account.validate()
    return trading_account.cost_of_goods_sold


def get_net_sales(trading_account: TradingAccount) -> Decimal:
    """Return net sales from a validated Trading Account."""
    trading_account.validate()
    return trading_account.net_sales


def get_net_purchases(
    trading_account: TradingAccount,
) -> Decimal:
    """Return net purchases from a validated Trading Account."""
    trading_account.validate()
    return trading_account.net_purchases