from __future__ import annotations

import random
from decimal import Decimal

from ..templates import get_all_templates
from .distributions import generate_amount, generate_date
from .schemas import GeneratedTransaction, GenerationConfig


_TRANSACTION_PHRASES = {
    "cash_sale": (
        "Cash sale of goods",
        "Goods sold for cash",
        "Cash sales",
    ),
    "credit_sale": (
        "Goods sold on credit",
        "Credit sale of goods",
        "Goods sold to customer on credit",
    ),
    "cash_purchase": (
        "Purchased goods for cash",
        "Cash purchase of goods",
        "Goods purchased for cash",
    ),
    "credit_purchase": (
        "Purchased goods on credit",
        "Credit purchase of goods",
        "Goods purchased on credit",
    ),
    "rent_paid": (
        "Rent paid",
        "Paid rent expense",
        "Rent expense paid",
    ),
    "salary_paid": (
        "Salary paid",
        "Paid salary",
        "Salary expense paid",
    ),
    "electricity_paid": (
        "Electricity bill paid",
        "Electricity expense paid",
        "Paid electricity expense",
    ),
    "transport_paid": (
        "Transport expense paid",
        "Transportation expense paid",
        "Paid transport expense",
    ),
    "commission_received": (
        "Commission received",
        "Received commission",
        "Commission income received",
    ),
    "interest_received": (
        "Interest received",
        "Received interest",
        "Interest income received",
    ),
    "capital_introduced": (
        "Capital introduced",
        "Capital invested",
        "Owner introduced capital",
    ),
    "drawings_cash": (
        "Cash drawings",
        "Owner drawings",
        "Cash withdrawn for personal use",
    ),
    "loan_received": (
        "Loan received",
        "Received loan",
        "Business borrowed money",
    ),
    "loan_repayment": (
        "Loan repayment",
        "Repaid loan",
        "Loan paid",
    ),
    "cash_deposited_bank": (
        "Cash deposited into bank",
        "Deposited cash in bank",
        "Cash transferred to bank",
    ),
    "cash_withdrawn_bank": (
        "Cash withdrawn from bank",
        "Withdrawn cash from bank",
        "Cash transferred from bank",
    ),
    "bad_debt": (
        "Bad debt written off",
        "Customer debt written off",
        "Receivable written off",
    ),
}


class TransactionGenerator:
    def __init__(self, config: GenerationConfig | None = None):
        self.config = config or GenerationConfig()
        self.config.validate()
        self.rng = random.Random(self.config.seed)

    def generate_one(self, index: int) -> GeneratedTransaction:
        templates = get_all_templates()

        template = self.rng.choice(templates)

        amount = generate_amount(
            self.rng,
            self.config.min_amount,
            self.config.max_amount,
        )

        transaction_date = generate_date(
            self.rng,
            self.config.start_date,
            self.config.end_date,
        )

        phrases = _TRANSACTION_PHRASES.get(
            template.template_id,
            (template.description,),
        )

        phrase = self.rng.choice(phrases)

        transaction_text = f"{phrase} {amount}"

        transaction = GeneratedTransaction(
            transaction_id=f"GEN-{self.config.seed:08d}-{index:08d}",
            date=transaction_date,
            transaction=transaction_text,
            amount=amount,
            template_id=template.template_id,
            debit_account=template.debit_account,
            credit_account=template.credit_account,
            category=template.category.value,
        )

        transaction.validate()

        return transaction

    def generate(self) -> list[GeneratedTransaction]:
        return [
            self.generate_one(index)
            for index in range(self.config.rows)
        ]


def generate_transactions(
    rows: int = 1000,
    seed: int = 42,
    start_date=None,
    end_date=None,
    min_amount: Decimal = Decimal("100"),
    max_amount: Decimal = Decimal("100000"),
) -> list[GeneratedTransaction]:
    config = GenerationConfig(
        rows=rows,
        seed=seed,
        start_date=start_date or GenerationConfig.start_date,
        end_date=end_date or GenerationConfig.end_date,
        min_amount=min_amount,
        max_amount=max_amount,
    )

    return TransactionGenerator(config).generate()
