from __future__ import annotations

from .schemas import AccountingTemplate, TemplateCategory


ACCOUNTING_TEMPLATES = (
    AccountingTemplate(
        template_id="cash_sale",
        name="Cash Sale",
        category=TemplateCategory.SALES,
        description="Goods sold for immediate cash consideration.",
        debit_account="Cash",
        credit_account="Sales",
        supports_cash=True,
        supports_credit=False,
    ),
    AccountingTemplate(
        template_id="credit_sale",
        name="Credit Sale",
        category=TemplateCategory.SALES,
        description="Goods sold on credit to a customer.",
        debit_account="Accounts Receivable",
        credit_account="Sales",
        supports_cash=False,
        supports_credit=True,
    ),
    AccountingTemplate(
        template_id="cash_purchase",
        name="Cash Purchase",
        category=TemplateCategory.PURCHASES,
        description="Goods purchased with immediate cash payment.",
        debit_account="Purchases",
        credit_account="Cash",
        supports_cash=True,
        supports_credit=False,
    ),
    AccountingTemplate(
        template_id="credit_purchase",
        name="Credit Purchase",
        category=TemplateCategory.PURCHASES,
        description="Goods purchased on credit from a supplier.",
        debit_account="Purchases",
        credit_account="Accounts Payable",
        supports_cash=False,
        supports_credit=True,
    ),
    AccountingTemplate(
        template_id="rent_paid",
        name="Rent Paid",
        category=TemplateCategory.EXPENSES,
        description="Rent expense paid through cash or bank.",
        debit_account="Rent Expense",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="salary_paid",
        name="Salary Paid",
        category=TemplateCategory.EXPENSES,
        description="Salary expense paid through cash or bank.",
        debit_account="Salary Expense",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="electricity_paid",
        name="Electricity Paid",
        category=TemplateCategory.EXPENSES,
        description="Electricity expense paid through cash or bank.",
        debit_account="Electricity Expense",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="transport_paid",
        name="Transport Expense Paid",
        category=TemplateCategory.EXPENSES,
        description="Transport expense paid through cash or bank.",
        debit_account="Transport Expense",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="commission_received",
        name="Commission Received",
        category=TemplateCategory.INCOME,
        description="Commission income received in cash or bank.",
        debit_account="Cash",
        credit_account="Commission Income",
    ),
    AccountingTemplate(
        template_id="interest_received",
        name="Interest Received",
        category=TemplateCategory.INCOME,
        description="Interest income received in cash or bank.",
        debit_account="Cash",
        credit_account="Interest Income",
    ),
    AccountingTemplate(
        template_id="capital_introduced",
        name="Capital Introduced",
        category=TemplateCategory.CAPITAL,
        description="Owner introduces capital into the business.",
        debit_account="Cash",
        credit_account="Capital",
    ),
    AccountingTemplate(
        template_id="drawings_cash",
        name="Cash Drawings",
        category=TemplateCategory.DRAWINGS,
        description="Owner withdraws cash for personal use.",
        debit_account="Drawings",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="loan_received",
        name="Loan Received",
        category=TemplateCategory.LOANS,
        description="Business receives a loan.",
        debit_account="Cash",
        credit_account="Loan Payable",
    ),
    AccountingTemplate(
        template_id="loan_repayment",
        name="Loan Repayment",
        category=TemplateCategory.LOANS,
        description="Business repays loan principal.",
        debit_account="Loan Payable",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="cash_deposited_bank",
        name="Cash Deposited Into Bank",
        category=TemplateCategory.BANKING,
        description="Cash transferred from cash account to bank account.",
        debit_account="Bank",
        credit_account="Cash",
    ),
    AccountingTemplate(
        template_id="cash_withdrawn_bank",
        name="Cash Withdrawn From Bank",
        category=TemplateCategory.BANKING,
        description="Cash withdrawn from bank for business use.",
        debit_account="Cash",
        credit_account="Bank",
    ),
    AccountingTemplate(
        template_id="bad_debt",
        name="Bad Debt",
        category=TemplateCategory.ADJUSTMENTS,
        description="Customer receivable written off as bad debt.",
        debit_account="Bad Debt Expense",
        credit_account="Accounts Receivable",
    ),
)


def get_all_templates() -> tuple[AccountingTemplate, ...]:
    return ACCOUNTING_TEMPLATES


def get_template(template_id: str) -> AccountingTemplate:
    normalized = template_id.strip().lower()

    for template in ACCOUNTING_TEMPLATES:
        if template.template_id == normalized:
            return template

    raise KeyError(f"Unknown accounting template: {template_id}")


def get_templates_by_category(
    category: TemplateCategory,
) -> tuple[AccountingTemplate, ...]:
    return tuple(
        template
        for template in ACCOUNTING_TEMPLATES
        if template.category == category
    )
