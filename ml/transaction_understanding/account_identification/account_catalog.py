from .schemas import AccountRecord


DEFAULT_ACCOUNT_CATALOG = (
    AccountRecord(
        account_id="cash",
        account_name="Cash",
        category="asset",
        keywords=(
            "cash",
            "cash in hand",
            "petty cash",
        ),
    ),
    AccountRecord(
        account_id="bank",
        account_name="Bank",
        category="asset",
        keywords=(
            "bank",
            "bank account",
            "bank transfer",
            "neft",
            "rtgs",
            "imps",
            "upi",
        ),
    ),
    AccountRecord(
        account_id="accounts_receivable",
        account_name="Accounts Receivable",
        category="asset",
        keywords=(
            "customer",
            "debtor",
            "receivable",
            "credit customer",
            "amount due",
        ),
    ),
    AccountRecord(
        account_id="inventory",
        account_name="Inventory",
        category="asset",
        keywords=(
            "inventory",
            "stock",
            "goods",
            "merchandise",
            "trading goods",
        ),
    ),
    AccountRecord(
        account_id="furniture",
        account_name="Furniture",
        category="asset",
        keywords=(
            "furniture",
            "desk",
            "chair",
            "table",
            "office furniture",
        ),
    ),
    AccountRecord(
        account_id="machinery",
        account_name="Machinery",
        category="asset",
        keywords=(
            "machinery",
            "machine",
            "manufacturing machine",
            "plant machine",
        ),
    ),
    AccountRecord(
        account_id="office_equipment",
        account_name="Office Equipment",
        category="asset",
        keywords=(
            "office equipment",
            "equipment",
            "printer",
            "scanner",
        ),
    ),
    AccountRecord(
        account_id="computer_equipment",
        account_name="Computer Equipment",
        category="asset",
        keywords=(
            "computer",
            "laptop",
            "desktop",
            "computer equipment",
        ),
    ),
    AccountRecord(
        account_id="accounts_payable",
        account_name="Accounts Payable",
        category="liability",
        keywords=(
            "supplier",
            "creditor",
            "payable",
            "vendor",
            "amount owed",
        ),
    ),
    AccountRecord(
        account_id="loan",
        account_name="Loan",
        category="liability",
        keywords=(
            "loan",
            "borrowed",
            "borrowing",
            "bank loan",
            "loan received",
        ),
    ),
    AccountRecord(
        account_id="capital",
        account_name="Capital",
        category="capital",
        keywords=(
            "capital",
            "owner capital",
            "proprietor capital",
            "owner investment",
            "introduced capital",
        ),
    ),
    AccountRecord(
        account_id="sales",
        account_name="Sales",
        category="income",
        keywords=(
            "sales",
            "sold",
            "goods sold",
            "sale",
            "revenue from sales",
        ),
    ),
    AccountRecord(
        account_id="commission_income",
        account_name="Commission Income",
        category="income",
        keywords=(
            "commission received",
            "commission income",
            "commission earned",
        ),
    ),
    AccountRecord(
        account_id="interest_income",
        account_name="Interest Income",
        category="income",
        keywords=(
            "interest received",
            "interest income",
            "interest earned",
            "bank interest",
        ),
    ),
    AccountRecord(
        account_id="miscellaneous_income",
        account_name="Miscellaneous Income",
        category="income",
        keywords=(
            "other income",
            "miscellaneous income",
            "dividend income",
        ),
    ),
    AccountRecord(
        account_id="purchases",
        account_name="Purchases",
        category="expense",
        keywords=(
            "purchase",
            "purchased",
            "bought goods",
            "goods purchased",
            "inventory purchase",
        ),
    ),
    AccountRecord(
        account_id="rent_expense",
        account_name="Rent Expense",
        category="expense",
        keywords=(
            "rent",
            "office rent",
            "shop rent",
            "building rent",
            "rental expense",
        ),
    ),
    AccountRecord(
        account_id="salary_expense",
        account_name="Salary Expense",
        category="expense",
        keywords=(
            "salary",
            "salaries",
            "employee salary",
            "staff salary",
            "wages",
            "employee wages",
        ),
    ),
    AccountRecord(
        account_id="utilities_expense",
        account_name="Utilities Expense",
        category="expense",
        keywords=(
            "electricity",
            "water bill",
            "gas bill",
            "utility",
            "utilities",
            "electricity bill",
        ),
    ),
    AccountRecord(
        account_id="transport_expense",
        account_name="Transport Expense",
        category="expense",
        keywords=(
            "transport",
            "freight",
            "delivery",
            "shipping",
            "transport charges",
        ),
    ),
    AccountRecord(
        account_id="advertising_expense",
        account_name="Advertising Expense",
        category="expense",
        keywords=(
            "advertising",
            "advertisement",
            "marketing",
            "promotion",
            "campaign",
        ),
    ),
    AccountRecord(
        account_id="commission_expense",
        account_name="Commission Expense",
        category="expense",
        keywords=(
            "commission paid",
            "sales commission",
            "commission expense",
        ),
    ),
    AccountRecord(
        account_id="interest_expense",
        account_name="Interest Expense",
        category="expense",
        keywords=(
            "interest paid",
            "interest expense",
            "loan interest",
        ),
    ),
    AccountRecord(
        account_id="tax_expense",
        account_name="Tax Expense",
        category="expense",
        keywords=(
            "tax",
            "gst",
            "income tax",
            "tax expense",
        ),
    ),
    AccountRecord(
        account_id="insurance_expense",
        account_name="Insurance Expense",
        category="expense",
        keywords=(
            "insurance",
            "insurance premium",
            "insurance expense",
        ),
    ),
    AccountRecord(
        account_id="miscellaneous_expense",
        account_name="Miscellaneous Expense",
        category="expense",
        keywords=(
            "miscellaneous expense",
            "other expense",
            "other business expense",
        ),
    ),
)


class AccountCatalog:
    """
    In-memory account catalog.

    Later this can be replaced by a PostgreSQL-backed
    repository without changing the identifier interface.
    """

    def __init__(
        self,
        accounts: tuple[AccountRecord, ...] = DEFAULT_ACCOUNT_CATALOG,
    ) -> None:
        if not accounts:
            raise ValueError(
                "Account catalog cannot be empty."
            )

        ids = [
            account.account_id
            for account in accounts
        ]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Account IDs must be unique."
            )

        self._accounts = tuple(accounts)

    @property
    def accounts(self) -> tuple[AccountRecord, ...]:
        return self._accounts

    def get(
        self,
        account_id: str,
    ) -> AccountRecord | None:
        for account in self._accounts:
            if account.account_id == account_id:
                return account

        return None

    def names(self) -> tuple[str, ...]:
        return tuple(
            account.account_name
            for account in self._accounts
        )

    def __len__(self) -> int:
        return len(self._accounts)
