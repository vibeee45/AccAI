from __future__ import annotations

import random
from decimal import Decimal

from ..generation import GeneratedTransaction
from .catalog import get_variation_phrases
from .schemas import TransactionVariation, VariationConfig


class VariationGenerator:
    def __init__(
        self,
        config: VariationConfig | None = None,
    ):
        self.config = config or VariationConfig()
        self.config.validate()
        self.rng = random.Random(self.config.seed)

    def generate_for_transaction(
        self,
        transaction: GeneratedTransaction,
    ) -> list[TransactionVariation]:
        phrases = list(
            get_variation_phrases(transaction.template_id)
        )

        if not phrases:
            raise LookupError(
                "No variation phrases configured for template: "
                f"{transaction.template_id}"
            )

        if self.config.variations_per_transaction <= len(phrases):
            selected = self.rng.sample(
                phrases,
                self.config.variations_per_transaction,
            )
        else:
            selected = [
                self.rng.choice(phrases)
                for _ in range(
                    self.config.variations_per_transaction
                )
            ]

        variations = []

        for index, phrase in enumerate(selected):
            text = phrase

            if self.config.include_amount:
                text = f"{text} {transaction.amount}"

            variation = TransactionVariation(
                variation_id=(
                    f"{transaction.transaction_id}"
                    f"-VAR-{index:03d}"
                ),
                template_id=transaction.template_id,
                transaction=text,
                amount=transaction.amount,
                debit_account=transaction.debit_account,
                credit_account=transaction.credit_account,
                category=transaction.category,
                source_transaction_id=transaction.transaction_id,
            )

            variation.validate()
            variations.append(variation)

        return variations

    def generate(
        self,
        transactions: list[GeneratedTransaction],
    ) -> list[TransactionVariation]:
        variations = []

        for transaction in transactions:
            variations.extend(
                self.generate_for_transaction(transaction)
            )

        return variations


def generate_variations(
    transactions: list[GeneratedTransaction],
    variations_per_transaction: int = 5,
    seed: int = 42,
    include_amount: bool = True,
) -> list[TransactionVariation]:
    config = VariationConfig(
        variations_per_transaction=variations_per_transaction,
        seed=seed,
        include_amount=include_amount,
    )

    return VariationGenerator(config).generate(transactions)
