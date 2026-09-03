from decimal import Decimal

import pytest

from app.accounting.trading import (
    TradingAccountError,
    generate_trading_account,
    get_cost_of_goods_sold,
    get_gross_loss,
    get_gross_profit,
    get_net_purchases,
    get_net_sales,
)


def test_trading_account_generates_gross_profit():
    trading = generate_trading_account(
        opening_stock="20000",
        purchases="100000",
        direct_expenses="10000",
        sales="180000",
        closing_stock="30000",
    )

    assert trading.net_purchases == Decimal("100000.00")
    assert trading.net_sales == Decimal("180000.00")
    assert trading.cost_of_goods_available == Decimal("130000.00")
    assert trading.cost_of_goods_sold == Decimal("100000.00")
    assert trading.gross_profit == Decimal("80000.00")
    assert trading.gross_loss == Decimal("0.00")
    assert trading.is_profit is True
    assert trading.is_loss is False
    assert trading.is_balanced is True


def test_trading_account_generates_gross_loss():
    trading = generate_trading_account(
        opening_stock="30000",
        purchases="100000",
        direct_expenses="10000",
        sales="110000",
        closing_stock="10000",
    )

    assert trading.cost_of_goods_sold == Decimal("130000.00")
    assert trading.net_sales == Decimal("110000.00")
    assert trading.gross_profit == Decimal("0.00")
    assert trading.gross_loss == Decimal("20000.00")
    assert trading.is_profit is False
    assert trading.is_loss is True
    assert trading.is_balanced is True


def test_purchase_returns_are_deducted_from_purchases():
    trading = generate_trading_account(
        purchases="100000",
        purchase_returns="15000",
        sales="150000",
        closing_stock="20000",
    )

    assert trading.net_purchases == Decimal("85000.00")
    assert trading.cost_of_goods_sold == Decimal("65000.00")
    assert trading.gross_profit == Decimal("85000.00")


def test_sales_returns_are_deducted_from_sales():
    trading = generate_trading_account(
        purchases="100000",
        sales="150000",
        sales_returns="10000",
        closing_stock="20000",
    )

    assert trading.net_sales == Decimal("140000.00")
    assert trading.cost_of_goods_sold == Decimal("80000.00")
    assert trading.gross_profit == Decimal("60000.00")


def test_direct_expenses_are_added_to_cost_of_goods():
    trading = generate_trading_account(
        purchases="100000",
        direct_expenses="20000",
        sales="160000",
        closing_stock="30000",
    )

    assert trading.cost_of_goods_available == Decimal("120000.00")
    assert trading.cost_of_goods_sold == Decimal("90000.00")
    assert trading.gross_profit == Decimal("70000.00")


def test_opening_and_closing_stock_are_included_correctly():
    trading = generate_trading_account(
        opening_stock="25000",
        purchases="100000",
        sales="180000",
        closing_stock="35000",
    )

    assert trading.cost_of_goods_available == Decimal("125000.00")
    assert trading.cost_of_goods_sold == Decimal("90000.00")
    assert trading.gross_profit == Decimal("90000.00")


def test_all_trading_account_components_together():
    trading = generate_trading_account(
        opening_stock="20000",
        purchases="120000",
        purchase_returns="10000",
        direct_expenses="15000",
        sales="200000",
        sales_returns="20000",
        closing_stock="30000",
    )

    assert trading.net_purchases == Decimal("110000.00")
    assert trading.net_sales == Decimal("180000.00")
    assert trading.cost_of_goods_available == Decimal("145000.00")
    assert trading.cost_of_goods_sold == Decimal("115000.00")
    assert trading.gross_profit == Decimal("65000.00")
    assert trading.gross_loss == Decimal("0.00")
    assert trading.is_balanced is True


def test_zero_values_are_supported():
    trading = generate_trading_account()

    assert trading.net_purchases == Decimal("0.00")
    assert trading.net_sales == Decimal("0.00")
    assert trading.cost_of_goods_available == Decimal("0.00")
    assert trading.cost_of_goods_sold == Decimal("0.00")
    assert trading.gross_profit == Decimal("0.00")
    assert trading.gross_loss == Decimal("0.00")
    assert trading.is_balanced is True


def test_purchase_returns_cannot_exceed_purchases():
    with pytest.raises(
        TradingAccountError,
        match="Purchase returns cannot exceed purchases",
    ):
        generate_trading_account(
            purchases="50000",
            purchase_returns="60000",
            sales="100000",
        )


def test_sales_returns_cannot_exceed_sales():
    with pytest.raises(
        TradingAccountError,
        match="Sales returns cannot exceed sales",
    ):
        generate_trading_account(
            purchases="50000",
            sales="50000",
            sales_returns="60000",
        )


def test_closing_stock_cannot_exceed_cost_of_goods_available():
    with pytest.raises(
        TradingAccountError,
        match="Closing stock cannot exceed cost of goods available",
    ):
        generate_trading_account(
            purchases="50000",
            sales="100000",
            closing_stock="60000",
        )


def test_negative_amount_is_rejected():
    with pytest.raises(
        TradingAccountError,
        match="Amount cannot be negative",
    ):
        generate_trading_account(
            purchases="-10000",
            sales="50000",
        )


def test_invalid_amount_is_rejected():
    with pytest.raises(TradingAccountError):
        generate_trading_account(
            purchases="not-a-number",
            sales="50000",
        )


def test_helper_functions_return_expected_values():
    trading = generate_trading_account(
        purchases="100000",
        sales="160000",
        closing_stock="20000",
    )

    assert get_net_purchases(trading) == Decimal("100000.00")
    assert get_net_sales(trading) == Decimal("160000.00")
    assert get_cost_of_goods_sold(trading) == Decimal("80000.00")
    assert get_gross_profit(trading) == Decimal("80000.00")
    assert get_gross_loss(trading) == Decimal("0.00")