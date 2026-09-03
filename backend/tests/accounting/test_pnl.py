from decimal import Decimal

import pytest

from app.accounting.pnl import (
    ProfitLossError,
    generate_pnl,
    generate_pnl_from_trading,
    get_net_loss,
    get_net_profit,
    get_total_expenses,
    get_total_income,
)
from app.accounting.trading import generate_trading_account


def test_pnl_generates_net_profit():
    pnl = generate_pnl(
        gross_profit="80000",
        indirect_incomes="10000",
        indirect_expenses="30000",
    )

    assert pnl.total_income == Decimal("90000.00")
    assert pnl.total_expenses == Decimal("30000.00")
    assert pnl.net_profit == Decimal("60000.00")
    assert pnl.net_loss == Decimal("0.00")
    assert pnl.is_profit is True
    assert pnl.is_loss is False
    assert pnl.is_balanced is True


def test_pnl_generates_net_loss():
    pnl = generate_pnl(
        gross_profit="40000",
        indirect_incomes="5000",
        indirect_expenses="60000",
    )

    assert pnl.total_income == Decimal("45000.00")
    assert pnl.total_expenses == Decimal("60000.00")
    assert pnl.net_profit == Decimal("0.00")
    assert pnl.net_loss == Decimal("15000.00")
    assert pnl.is_profit is False
    assert pnl.is_loss is True
    assert pnl.is_balanced is True


def test_indirect_income_is_added_to_gross_profit():
    pnl = generate_pnl(
        gross_profit="100000",
        indirect_incomes="25000",
        indirect_expenses="20000",
    )

    assert pnl.total_income == Decimal("125000.00")
    assert pnl.net_profit == Decimal("105000.00")


def test_indirect_expenses_are_deducted_from_income():
    pnl = generate_pnl(
        gross_profit="100000",
        indirect_expenses="35000",
    )

    assert pnl.total_income == Decimal("100000.00")
    assert pnl.total_expenses == Decimal("35000.00")
    assert pnl.net_profit == Decimal("65000.00")


def test_pnl_works_with_gross_loss():
    pnl = generate_pnl(
        gross_loss="20000",
        indirect_incomes="5000",
        indirect_expenses="10000",
    )

    assert pnl.total_income == Decimal("5000.00")
    assert pnl.total_expenses == Decimal("30000.00")
    assert pnl.net_profit == Decimal("0.00")
    assert pnl.net_loss == Decimal("25000.00")
    assert pnl.is_loss is True
    assert pnl.is_balanced is True


def test_gross_profit_and_gross_loss_cannot_both_exist():
    with pytest.raises(
        ProfitLossError,
        match="Gross profit and gross loss cannot both be present",
    ):
        generate_pnl(
            gross_profit="50000",
            gross_loss="10000",
            indirect_expenses="5000",
        )


def test_negative_gross_profit_is_rejected():
    with pytest.raises(
        ProfitLossError,
        match="Amount cannot be negative",
    ):
        generate_pnl(
            gross_profit="-50000",
        )


def test_negative_indirect_income_is_rejected():
    with pytest.raises(
        ProfitLossError,
        match="Amount cannot be negative",
    ):
        generate_pnl(
            indirect_incomes="-10000",
        )


def test_negative_indirect_expense_is_rejected():
    with pytest.raises(
        ProfitLossError,
        match="Amount cannot be negative",
    ):
        generate_pnl(
            indirect_expenses="-10000",
        )


def test_invalid_amount_is_rejected():
    with pytest.raises(ProfitLossError):
        generate_pnl(
            gross_profit="invalid",
        )


def test_zero_values_are_supported():
    pnl = generate_pnl()

    assert pnl.total_income == Decimal("0.00")
    assert pnl.total_expenses == Decimal("0.00")
    assert pnl.net_profit == Decimal("0.00")
    assert pnl.net_loss == Decimal("0.00")
    assert pnl.is_profit is False
    assert pnl.is_loss is False
    assert pnl.is_balanced is True


def test_pnl_from_trading_account():
    trading = generate_trading_account(
        opening_stock="20000",
        purchases="100000",
        direct_expenses="10000",
        sales="180000",
        closing_stock="30000",
    )

    pnl = generate_pnl_from_trading(
        trading,
        indirect_incomes="10000",
        indirect_expenses="30000",
    )

    # Trading Account:
    # COGS = 20,000 + 100,000 + 10,000 - 30,000
    #      = 100,000
    #
    # Gross Profit = 180,000 - 100,000
    #              = 80,000
    #
    # P&L:
    # Income = 80,000 + 10,000 = 90,000
    # Expenses = 30,000
    # Net Profit = 60,000

    assert pnl.gross_profit == Decimal("80000.00")
    assert pnl.gross_loss == Decimal("0.00")
    assert pnl.total_income == Decimal("90000.00")
    assert pnl.total_expenses == Decimal("30000.00")
    assert pnl.net_profit == Decimal("60000.00")
    assert pnl.net_loss == Decimal("0.00")


def test_pnl_from_trading_gross_loss():
    trading = generate_trading_account(
        opening_stock="30000",
        purchases="100000",
        direct_expenses="10000",
        sales="110000",
        closing_stock="10000",
    )

    pnl = generate_pnl_from_trading(
        trading,
        indirect_incomes="5000",
        indirect_expenses="10000",
    )

    assert pnl.gross_profit == Decimal("0.00")
    assert pnl.gross_loss == Decimal("20000.00")
    assert pnl.total_income == Decimal("5000.00")
    assert pnl.total_expenses == Decimal("30000.00")
    assert pnl.net_loss == Decimal("25000.00")


def test_helper_functions_return_expected_values():
    pnl = generate_pnl(
        gross_profit="80000",
        indirect_incomes="10000",
        indirect_expenses="30000",
    )

    assert get_total_income(pnl) == Decimal("90000.00")
    assert get_total_expenses(pnl) == Decimal("30000.00")
    assert get_net_profit(pnl) == Decimal("60000.00")
    assert get_net_loss(pnl) == Decimal("0.00")


def test_pnl_calculate_returns_validated_instance():
    pnl = generate_pnl(
        gross_profit="50000",
        indirect_incomes="10000",
        indirect_expenses="15000",
    )

    calculated = pnl.calculate()

    assert calculated is pnl
    assert calculated.net_profit == Decimal("45000.00")
    assert calculated.is_balanced is True