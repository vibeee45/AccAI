from decimal import Decimal

import pytest

from app.accounting.balance_sheet import (
    BalanceSheetError,
    generate_balance_sheet,
    generate_balance_sheet_from_pnl,
    get_adjusted_capital,
    get_balance_sheet_difference,
    get_total_assets,
    get_total_equity,
    get_total_liabilities,
)
from app.accounting.pnl import generate_pnl


def test_balanced_balance_sheet():
    balance_sheet = generate_balance_sheet(
        fixed_assets=[
            ("Machinery", "200000"),
            ("Furniture", "50000"),
        ],
        current_assets=[
            ("Cash", "100000"),
            ("Bank", "150000"),
        ],
        liabilities=[
            ("Creditors", "100000"),
        ],
        capital="350000",
        net_profit="50000",
    )

    assert balance_sheet.total_fixed_assets == Decimal("250000.00")
    assert balance_sheet.total_current_assets == Decimal("250000.00")
    assert balance_sheet.total_assets == Decimal("500000.00")

    assert balance_sheet.total_liabilities == Decimal("100000.00")
    assert balance_sheet.adjusted_capital == Decimal("400000.00")
    assert balance_sheet.total_equity == Decimal("400000.00")

    assert balance_sheet.liabilities_and_equity == Decimal("500000.00")
    assert balance_sheet.difference == Decimal("0.00")
    assert balance_sheet.is_balanced is True


def test_fixed_and_current_assets_are_calculated_separately():
    balance_sheet = generate_balance_sheet(
        fixed_assets=[
            ("Building", "300000"),
            ("Machinery", "100000"),
        ],
        current_assets=[
            ("Cash", "50000"),
            ("Inventory", "75000"),
            ("Debtors", "25000"),
        ],
        liabilities=[
            ("Creditors", "50000"),
        ],
        capital="500000",
    )

    assert balance_sheet.total_fixed_assets == Decimal("400000.00")
    assert balance_sheet.total_current_assets == Decimal("150000.00")
    assert balance_sheet.total_assets == Decimal("550000.00")

    assert balance_sheet.total_liabilities == Decimal("50000.00")
    assert balance_sheet.adjusted_capital == Decimal("500000.00")

    assert balance_sheet.liabilities_and_equity == Decimal("550000.00")
    assert balance_sheet.is_balanced is True


def test_multiple_liabilities_are_summed():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "150000"),
        ],
        liabilities=[
            ("Creditors", "30000"),
            ("Bank Loan", "20000"),
        ],
        capital="100000",
    )

    assert balance_sheet.total_assets == Decimal("150000.00")
    assert balance_sheet.total_liabilities == Decimal("50000.00")
    assert balance_sheet.adjusted_capital == Decimal("100000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("150000.00")
    assert balance_sheet.is_balanced is True


def test_net_profit_increases_capital():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "150000"),
        ],
        liabilities=[
            ("Creditors", "50000"),
        ],
        capital="80000",
        net_profit="20000",
    )

    assert balance_sheet.adjusted_capital == Decimal("100000.00")
    assert balance_sheet.total_equity == Decimal("100000.00")
    assert balance_sheet.total_assets == Decimal("150000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("150000.00")
    assert balance_sheet.is_balanced is True


def test_net_loss_reduces_capital():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "80000"),
        ],
        liabilities=[
            ("Creditors", "30000"),
        ],
        capital="70000",
        net_loss="20000",
    )

    assert balance_sheet.adjusted_capital == Decimal("50000.00")
    assert balance_sheet.total_equity == Decimal("50000.00")
    assert balance_sheet.total_assets == Decimal("80000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("80000.00")
    assert balance_sheet.is_balanced is True


def test_drawings_reduce_capital():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "90000"),
        ],
        liabilities=[
            ("Creditors", "20000"),
        ],
        capital="80000",
        drawings="10000",
    )

    assert balance_sheet.adjusted_capital == Decimal("70000.00")
    assert balance_sheet.total_equity == Decimal("70000.00")
    assert balance_sheet.total_assets == Decimal("90000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("90000.00")
    assert balance_sheet.is_balanced is True


def test_profit_and_drawings_together():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "150000"),
        ],
        liabilities=[
            ("Loan", "50000"),
        ],
        capital="90000",
        net_profit="20000",
        drawings="10000",
    )

    # Adjusted Capital
    # = 90,000 + 20,000 - 10,000
    # = 100,000

    assert balance_sheet.adjusted_capital == Decimal("100000.00")
    assert balance_sheet.total_assets == Decimal("150000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("150000.00")
    assert balance_sheet.is_balanced is True


def test_balance_sheet_from_pnl_profit():
    pnl = generate_pnl(
        gross_profit="80000",
        indirect_incomes="10000",
        indirect_expenses="30000",
    )

    balance_sheet = generate_balance_sheet_from_pnl(
        pnl,
        current_assets=[
            ("Cash", "120000"),
        ],
        liabilities=[
            ("Creditors", "20000"),
        ],
        capital="40000",
    )

    assert pnl.net_profit == Decimal("60000.00")
    assert balance_sheet.net_profit == Decimal("60000.00")
    assert balance_sheet.net_loss == Decimal("0.00")

    assert balance_sheet.adjusted_capital == Decimal("100000.00")
    assert balance_sheet.total_assets == Decimal("120000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("120000.00")
    assert balance_sheet.is_balanced is True


def test_balance_sheet_from_pnl_loss():
    pnl = generate_pnl(
        gross_loss="20000",
        indirect_incomes="5000",
        indirect_expenses="10000",
    )

    balance_sheet = generate_balance_sheet_from_pnl(
        pnl,
        current_assets=[
            ("Cash", "80000"),
        ],
        liabilities=[
            ("Creditors", "30000"),
        ],
        capital="70000",
    )

    assert pnl.net_loss == Decimal("25000.00")
    assert balance_sheet.net_profit == Decimal("0.00")
    assert balance_sheet.net_loss == Decimal("25000.00")

    assert balance_sheet.adjusted_capital == Decimal("45000.00")
    assert balance_sheet.total_assets == Decimal("80000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("75000.00")
    assert balance_sheet.is_balanced is False


def test_generate_balance_sheet_from_pnl_preserves_pnl_result():
    pnl = generate_pnl(
        gross_profit="100000",
        indirect_incomes="20000",
        indirect_expenses="40000",
    )

    balance_sheet = generate_balance_sheet_from_pnl(
        pnl,
        current_assets=[
            ("Cash", "220000"),
        ],
        liabilities=[
            ("Creditors", "50000"),
        ],
        capital="90000",
    )

    assert pnl.net_profit == Decimal("80000.00")
    assert balance_sheet.net_profit == Decimal("80000.00")
    assert balance_sheet.net_loss == Decimal("0.00")

    assert balance_sheet.adjusted_capital == Decimal("170000.00")
    assert balance_sheet.total_assets == Decimal("220000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("220000.00")
    assert balance_sheet.difference == Decimal("0.00")
    assert balance_sheet.is_balanced is True


def test_negative_capital_is_rejected():
    with pytest.raises(
        BalanceSheetError,
        match="Amount cannot be negative",
    ):
        generate_balance_sheet(
            current_assets=[
                ("Cash", "100000"),
            ],
            capital="-50000",
        )


def test_negative_asset_is_rejected():
    with pytest.raises(
        BalanceSheetError,
        match="Amount cannot be negative",
    ):
        generate_balance_sheet(
            current_assets=[
                ("Cash", "-10000"),
            ],
            capital="10000",
        )


def test_negative_liability_is_rejected():
    with pytest.raises(
        BalanceSheetError,
        match="Amount cannot be negative",
    ):
        generate_balance_sheet(
            liabilities=[
                ("Loan", "-50000"),
            ],
            capital="50000",
        )


def test_negative_drawings_are_rejected():
    with pytest.raises(
        BalanceSheetError,
        match="Amount cannot be negative",
    ):
        generate_balance_sheet(
            current_assets=[
                ("Cash", "100000"),
            ],
            capital="100000",
            drawings="-5000",
        )


def test_profit_and_loss_cannot_both_exist():
    with pytest.raises(
        BalanceSheetError,
        match="Net profit and net loss cannot both be present",
    ):
        generate_balance_sheet(
            current_assets=[
                ("Cash", "100000"),
            ],
            capital="100000",
            net_profit="10000",
            net_loss="5000",
        )


def test_drawings_cannot_exceed_available_capital_and_profit():
    with pytest.raises(
        BalanceSheetError,
        match="Drawings cannot exceed available capital and profit",
    ):
        generate_balance_sheet(
            current_assets=[
                ("Cash", "100000"),
            ],
            capital="50000",
            net_profit="10000",
            drawings="70000",
        )


def test_empty_account_name_is_rejected():
    with pytest.raises(
        BalanceSheetError,
        match="Account name cannot be empty",
    ):
        generate_balance_sheet(
            current_assets=[
                ("", "100000"),
            ],
            capital="100000",
        )


def test_invalid_amount_is_rejected():
    with pytest.raises(BalanceSheetError):
        generate_balance_sheet(
            current_assets=[
                ("Cash", "not-a-number"),
            ],
            capital="100000",
        )


def test_zero_values_are_supported():
    balance_sheet = generate_balance_sheet()

    assert balance_sheet.total_fixed_assets == Decimal("0.00")
    assert balance_sheet.total_current_assets == Decimal("0.00")
    assert balance_sheet.total_assets == Decimal("0.00")

    assert balance_sheet.total_liabilities == Decimal("0.00")
    assert balance_sheet.adjusted_capital == Decimal("0.00")
    assert balance_sheet.total_equity == Decimal("0.00")

    assert balance_sheet.liabilities_and_equity == Decimal("0.00")
    assert balance_sheet.difference == Decimal("0.00")
    assert balance_sheet.is_balanced is True


def test_balance_sheet_difference_detects_imbalance():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "100000"),
        ],
        capital="60000",
    )

    assert balance_sheet.total_assets == Decimal("100000.00")
    assert balance_sheet.liabilities_and_equity == Decimal("60000.00")
    assert balance_sheet.difference == Decimal("40000.00")
    assert balance_sheet.is_balanced is False

    with pytest.raises(
        BalanceSheetError,
        match="Balance Sheet is not balanced",
    ):
        balance_sheet.calculate()


def test_calculate_returns_same_valid_balance_sheet():
    balance_sheet = generate_balance_sheet(
        current_assets=[
            ("Cash", "150000"),
        ],
        liabilities=[
            ("Loan", "50000"),
        ],
        capital="100000",
    )

    calculated = balance_sheet.calculate()

    assert calculated is balance_sheet
    assert calculated.is_balanced is True
    assert calculated.difference == Decimal("0.00")


def test_helper_functions_return_expected_values():
    balance_sheet = generate_balance_sheet(
        fixed_assets=[
            ("Machinery", "100000"),
        ],
        current_assets=[
            ("Cash", "50000"),
        ],
        liabilities=[
            ("Loan", "30000"),
        ],
        capital="100000",
        net_profit="20000",
    )

    assert get_total_assets(balance_sheet) == Decimal("150000.00")
    assert get_total_liabilities(balance_sheet) == Decimal("30000.00")
    assert get_adjusted_capital(balance_sheet) == Decimal("120000.00")
    assert get_total_equity(balance_sheet) == Decimal("120000.00")
    assert get_balance_sheet_difference(balance_sheet) == Decimal("0.00")