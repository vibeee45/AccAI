from __future__ import annotations

from .schemas import AccountEntity, AccountType


CUSTOMERS = (
    AccountEntity(
        entity_id="customer_001",
        name="Rahul Traders",
        account_name="Accounts Receivable",
        account_type=AccountType.CUSTOMER,
    ),
    AccountEntity(
        entity_id="customer_002",
        name="Sharma Enterprises",
        account_name="Accounts Receivable",
        account_type=AccountType.CUSTOMER,
    ),
    AccountEntity(
        entity_id="customer_003",
        name="Apex Retail",
        account_name="Accounts Receivable",
        account_type=AccountType.CUSTOMER,
    ),
    AccountEntity(
        entity_id="customer_004",
        name="Global Mart",
        account_name="Accounts Receivable",
        account_type=AccountType.CUSTOMER,
    ),
    AccountEntity(
        entity_id="customer_005",
        name="City Distributors",
        account_name="Accounts Receivable",
        account_type=AccountType.CUSTOMER,
    ),
)


SUPPLIERS = (
    AccountEntity(
        entity_id="supplier_001",
        name="ABC Suppliers",
        account_name="Accounts Payable",
        account_type=AccountType.SUPPLIER,
    ),
    AccountEntity(
        entity_id="supplier_002",
        name="Shree Enterprises",
        account_name="Accounts Payable",
        account_type=AccountType.SUPPLIER,
    ),
    AccountEntity(
        entity_id="supplier_003",
        name="National Traders",
        account_name="Accounts Payable",
        account_type=AccountType.SUPPLIER,
    ),
    AccountEntity(
        entity_id="supplier_004",
        name="Metro Wholesale",
        account_name="Accounts Payable",
        account_type=AccountType.SUPPLIER,
    ),
    AccountEntity(
        entity_id="supplier_005",
        name="Prime Distributors",
        account_name="Accounts Payable",
        account_type=AccountType.SUPPLIER,
    ),
)


BANKS = (
    AccountEntity(
        entity_id="bank_001",
        name="State Bank",
        account_name="Bank",
        account_type=AccountType.BANK,
    ),
    AccountEntity(
        entity_id="bank_002",
        name="National Bank",
        account_name="Bank",
        account_type=AccountType.BANK,
    ),
)


CASH_ACCOUNT = AccountEntity(
    entity_id="cash_001",
    name="Cash",
    account_name="Cash",
    account_type=AccountType.CASH,
)


SALES_ACCOUNT = AccountEntity(
    entity_id="sales_001",
    name="Sales",
    account_name="Sales",
    account_type=AccountType.INCOME,
)


PURCHASES_ACCOUNT = AccountEntity(
    entity_id="purchases_001",
    name="Purchases",
    account_name="Purchases",
    account_type=AccountType.ASSET,
)


RENT_ACCOUNT = AccountEntity(
    entity_id="expense_rent",
    name="Rent Expense",
    account_name="Rent Expense",
    account_type=AccountType.EXPENSE,
)


SALARY_ACCOUNT = AccountEntity(
    entity_id="expense_salary",
    name="Salary Expense",
    account_name="Salary Expense",
    account_type=AccountType.EXPENSE,
)


ELECTRICITY_ACCOUNT = AccountEntity(
    entity_id="expense_electricity",
    name="Electricity Expense",
    account_name="Electricity Expense",
    account_type=AccountType.EXPENSE,
)


TRANSPORT_ACCOUNT = AccountEntity(
    entity_id="expense_transport",
    name="Transport Expense",
    account_name="Transport Expense",
    account_type=AccountType.EXPENSE,
)


CAPITAL_ACCOUNT = AccountEntity(
    entity_id="capital_001",
    name="Capital",
    account_name="Capital",
    account_type=AccountType.EQUITY,
)


DRAWINGS_ACCOUNT = AccountEntity(
    entity_id="drawings_001",
    name="Drawings",
    account_name="Drawings",
    account_type=AccountType.EQUITY,
)


LOAN_ACCOUNT = AccountEntity(
    entity_id="loan_001",
    name="Loan Payable",
    account_name="Loan Payable",
    account_type=AccountType.LIABILITY,
)


def get_customers() -> tuple[AccountEntity, ...]:
    return CUSTOMERS


def get_suppliers() -> tuple[AccountEntity, ...]:
    return SUPPLIERS


def get_banks() -> tuple[AccountEntity, ...]:
    return BANKS


def get_cash_account() -> AccountEntity:
    return CASH_ACCOUNT


def get_account_by_name(account_name: str) -> AccountEntity:
    normalized = account_name.strip().lower()

    accounts = (
        *CUSTOMERS,
        *SUPPLIERS,
        *BANKS,
        CASH_ACCOUNT,
        SALES_ACCOUNT,
        PURCHASES_ACCOUNT,
        RENT_ACCOUNT,
        SALARY_ACCOUNT,
        ELECTRICITY_ACCOUNT,
        TRANSPORT_ACCOUNT,
        CAPITAL_ACCOUNT,
        DRAWINGS_ACCOUNT,
        LOAN_ACCOUNT,
    )

    for account in accounts:
        if account.account_name.lower() == normalized:
            return account

    raise KeyError(f"Unknown account: {account_name}")
