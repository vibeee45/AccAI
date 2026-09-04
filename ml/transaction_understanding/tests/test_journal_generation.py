from decimal import Decimal

import pytest

from ml.transaction_understanding.accounting_adapter import (
    AccountingAccount,
    AccountingTransaction,
)

from ml.transaction_understanding.journal_generation import (
    JournalEntry,
    JournalGenerationConfig,
    JournalGenerationResult,
    JournalGenerationService,
    JournalGenerator,
    JournalLine,
)


def make_transaction(
    amount=Decimal("1000.00"),
):
    return AccountingTransaction(
        transaction_id="txn-001",
        description="cash sale",
        amount=amount,
        debit_account=AccountingAccount(
            "cash",
            "Cash",
        ),
        credit_account=AccountingAccount(
            "sales",
            "Sales",
        ),
        transaction_class="sales",
        payment_mode="cash",
        ai_confidence=0.96,
        requires_review=False,
        source_text="cash sale",
        normalized_text="cash sale",
        metadata={
            "source": "excel",
            "row": 5,
        },
    )


def test_config_defaults():
    config = JournalGenerationConfig()

    assert config.require_positive_amount is True
    assert config.require_distinct_accounts is True
    assert config.generate_narration is True


def test_config_custom_values():
    config = JournalGenerationConfig(
        require_positive_amount=False,
        require_distinct_accounts=False,
        generate_narration=False,
    )

    assert config.require_positive_amount is False
    assert config.require_distinct_accounts is False
    assert config.generate_narration is False


def test_config_rejects_invalid_boolean():
    with pytest.raises(TypeError):
        JournalGenerationConfig(
            require_positive_amount="yes"
        )


def test_journal_line_debit():
    line = JournalLine(
        account_id="cash",
        account_name="Cash",
        description="cash sale",
        debit=Decimal("1000"),
        credit=Decimal("0"),
    )

    assert line.debit == Decimal("1000")
    assert line.credit == Decimal("0")


def test_journal_line_credit():
    line = JournalLine(
        account_id="sales",
        account_name="Sales",
        description="cash sale",
        debit=Decimal("0"),
        credit=Decimal("1000"),
    )

    assert line.debit == Decimal("0")
    assert line.credit == Decimal("1000")


def test_journal_line_rejects_negative_debit():
    with pytest.raises(ValueError):
        JournalLine(
            account_id="cash",
            account_name="Cash",
            description="test",
            debit=Decimal("-100"),
            credit=Decimal("0"),
        )


def test_journal_line_rejects_negative_credit():
    with pytest.raises(ValueError):
        JournalLine(
            account_id="sales",
            account_name="Sales",
            description="test",
            debit=Decimal("0"),
            credit=Decimal("-100"),
        )


def test_journal_line_rejects_both_sides():
    with pytest.raises(ValueError):
        JournalLine(
            account_id="cash",
            account_name="Cash",
            description="test",
            debit=Decimal("100"),
            credit=Decimal("100"),
        )


def test_journal_line_rejects_zero_line():
    with pytest.raises(ValueError):
        JournalLine(
            account_id="cash",
            account_name="Cash",
            description="test",
            debit=Decimal("0"),
            credit=Decimal("0"),
        )


def test_generator_success():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert result.success is True
    assert result.journal is not None


def test_journal_id():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert result.journal.journal_id == "JE-txn-001"


def test_transaction_id():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert result.journal.transaction_id == "txn-001"


def test_journal_amount():
    result = JournalGenerator().generate(
        make_transaction(
            Decimal("2500.50")
        )
    )

    assert result.journal.amount == Decimal("2500.50")


def test_journal_has_two_lines():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert len(result.journal.lines) == 2


def test_first_line_is_debit():
    result = JournalGenerator().generate(
        make_transaction()
    )

    line = result.journal.lines[0]

    assert line.account_id == "cash"
    assert line.debit == Decimal("1000.00")
    assert line.credit == Decimal("0")


def test_second_line_is_credit():
    result = JournalGenerator().generate(
        make_transaction()
    )

    line = result.journal.lines[1]

    assert line.account_id == "sales"
    assert line.debit == Decimal("0")
    assert line.credit == Decimal("1000.00")


def test_journal_is_balanced():
    result = JournalGenerator().generate(
        make_transaction(
            Decimal("5000.75")
        )
    )

    journal = result.journal

    total_debit = sum(
        (
            line.debit
            for line in journal.lines
        ),
        Decimal("0"),
    )

    total_credit = sum(
        (
            line.credit
            for line in journal.lines
        ),
        Decimal("0"),
    )

    assert total_debit == Decimal("5000.75")
    assert total_credit == Decimal("5000.75")
    assert total_debit == total_credit


def test_narration():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert result.journal.narration == "cash sale"


def test_transaction_class():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert (
        result.journal.transaction_class
        == "sales"
    )


def test_payment_mode():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert result.journal.payment_mode == "cash"


def test_confidence_preserved():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert result.journal.ai_confidence == 0.96


def test_review_status_preserved():
    transaction = make_transaction()

    transaction = AccountingTransaction(
        transaction_id=transaction.transaction_id,
        description=transaction.description,
        amount=transaction.amount,
        debit_account=transaction.debit_account,
        credit_account=transaction.credit_account,
        transaction_class=transaction.transaction_class,
        payment_mode=transaction.payment_mode,
        ai_confidence=transaction.ai_confidence,
        requires_review=True,
        source_text=transaction.source_text,
        normalized_text=transaction.normalized_text,
        metadata=transaction.metadata,
    )

    result = JournalGenerator().generate(
        transaction
    )

    assert (
        result.journal.requires_review
        is True
    )


def test_metadata_preserved():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert (
        result.journal.metadata["source"]
        == "excel"
    )

    assert (
        result.journal.metadata["row"]
        == 5
    )


def test_description_preserved_on_lines():
    result = JournalGenerator().generate(
        make_transaction()
    )

    assert (
        result.journal.lines[0].description
        == "cash sale"
    )

    assert (
        result.journal.lines[1].description
        == "cash sale"
    )


def test_negative_amount_rejected_by_accounting_transaction():
    with pytest.raises(ValueError):
        make_transaction(
            Decimal("-100")
        )


def test_zero_amount_rejected_by_accounting_transaction():
    with pytest.raises(ValueError):
        make_transaction(
            Decimal("0")
        )


def test_invalid_input_type():
    with pytest.raises(TypeError):
        JournalGenerator().generate(
            "invalid"
        )


def test_same_accounts_rejected_by_accounting_transaction():
    with pytest.raises(ValueError):
        AccountingTransaction(
            transaction_id="txn-invalid",
            description="invalid transaction",
            amount=Decimal("1000"),
            debit_account=AccountingAccount(
                "cash",
                "Cash",
            ),
            credit_account=AccountingAccount(
                "cash",
                "Cash",
            ),
            transaction_class="sales",
            payment_mode="cash",
            ai_confidence=0.95,
            requires_review=False,
            source_text="invalid",
            normalized_text="invalid",
        )


def test_generate_many():
    generator = JournalGenerator()

    transactions = (
        make_transaction(Decimal("1000")),
        make_transaction(Decimal("2000")),
        make_transaction(Decimal("3000")),
    )

    results = generator.generate_many(
        transactions
    )

    assert len(results) == 3
    assert all(
        result.success
        for result in results
    )


def test_generate_many_amounts():
    generator = JournalGenerator()

    transactions = (
        make_transaction(Decimal("1000")),
        make_transaction(Decimal("2000")),
    )

    results = generator.generate_many(
        transactions
    )

    assert (
        results[0].journal.amount
        == Decimal("1000")
    )

    assert (
        results[1].journal.amount
        == Decimal("2000")
    )


def test_service_generate():
    service = JournalGenerationService()

    result = service.generate(
        make_transaction()
    )

    assert result.success is True


def test_service_generate_many():
    service = JournalGenerationService()

    results = service.generate_many(
        (
            make_transaction(),
            make_transaction(
                Decimal("2500")
            ),
        )
    )

    assert len(results) == 2
    assert all(
        result.success
        for result in results
    )


def test_service_ready():
    service = JournalGenerationService()

    assert service.is_ready() is True


def test_successful_result_requires_journal():
    with pytest.raises(ValueError):
        JournalGenerationResult(
            success=True,
            journal=None,
        )


def test_failed_result_cannot_have_journal():
    journal = JournalEntry(
        journal_id="JE-001",
        transaction_id="txn-001",
        narration="cash sale",
        amount=Decimal("1000"),
        lines=(
            JournalLine(
                account_id="cash",
                account_name="Cash",
                description="cash sale",
                debit=Decimal("1000"),
                credit=Decimal("0"),
            ),
            JournalLine(
                account_id="sales",
                account_name="Sales",
                description="cash sale",
                debit=Decimal("0"),
                credit=Decimal("1000"),
            ),
        ),
        transaction_class="sales",
        payment_mode="cash",
        ai_confidence=0.95,
        requires_review=False,
    )

    with pytest.raises(ValueError):
        JournalGenerationResult(
            success=False,
            journal=journal,
        )


def test_journal_entry_rejects_unbalanced_lines():
    with pytest.raises(ValueError):
        JournalEntry(
            journal_id="JE-001",
            transaction_id="txn-001",
            narration="invalid entry",
            amount=Decimal("1000"),
            lines=(
                JournalLine(
                    account_id="cash",
                    account_name="Cash",
                    description="invalid",
                    debit=Decimal("1000"),
                    credit=Decimal("0"),
                ),
                JournalLine(
                    account_id="sales",
                    account_name="Sales",
                    description="invalid",
                    debit=Decimal("0"),
                    credit=Decimal("500"),
                ),
            ),
            transaction_class="sales",
            payment_mode="cash",
            ai_confidence=0.95,
            requires_review=False,
        )


def test_journal_entry_rejects_wrong_total():
    with pytest.raises(ValueError):
        JournalEntry(
            journal_id="JE-001",
            transaction_id="txn-001",
            narration="wrong total",
            amount=Decimal("2000"),
            lines=(
                JournalLine(
                    account_id="cash",
                    account_name="Cash",
                    description="wrong total",
                    debit=Decimal("1000"),
                    credit=Decimal("0"),
                ),
                JournalLine(
                    account_id="sales",
                    account_name="Sales",
                    description="wrong total",
                    debit=Decimal("0"),
                    credit=Decimal("1000"),
                ),
            ),
            transaction_class="sales",
            payment_mode="cash",
            ai_confidence=0.95,
            requires_review=False,
        )


def test_decimal_precision_is_preserved():
    result = JournalGenerator().generate(
        make_transaction(
            Decimal("123456789.1234")
        )
    )

    journal = result.journal

    assert (
        journal.amount
        == Decimal("123456789.1234")
    )

    assert (
        journal.lines[0].debit
        == Decimal("123456789.1234")
    )

    assert (
        journal.lines[1].credit
        == Decimal("123456789.1234")
    )


def test_generator_accepts_decimal_amount():
    transaction = make_transaction(
        Decimal("1500.25")
    )

    result = JournalGenerator().generate(
        transaction
    )

    assert result.success is True
    assert (
        result.journal.amount
        == Decimal("1500.25")
    )


def test_float_amount_can_be_converted():
    transaction = make_transaction(
        1500.25
    )

    result = JournalGenerator().generate(
        transaction
    )

    assert result.success is True
    assert (
        result.journal.amount
        == Decimal("1500.25")
    )


def test_narration_can_be_disabled():
    config = JournalGenerationConfig(
        generate_narration=False
    )

    result = JournalGenerator(
        config
    ).generate(
        make_transaction()
    )

    assert (
        result.journal.narration
        == "sales transaction"
    )


def test_journal_lines_use_same_transaction_amount():
    result = JournalGenerator().generate(
        make_transaction(
            Decimal("9999.99")
        )
    )

    journal = result.journal

    assert (
        journal.lines[0].debit
        == journal.amount
    )

    assert (
        journal.lines[1].credit
        == journal.amount
    )


def test_no_zero_amount_journal_line():
    result = JournalGenerator().generate(
        make_transaction()
    )

    for line in result.journal.lines:
        assert (
            line.debit > Decimal("0")
            or line.credit > Decimal("0")
        )


def test_journal_contains_exactly_one_debit_line():
    result = JournalGenerator().generate(
        make_transaction()
    )

    debit_lines = [
        line
        for line in result.journal.lines
        if line.debit > Decimal("0")
    ]

    assert len(debit_lines) == 1


def test_journal_contains_exactly_one_credit_line():
    result = JournalGenerator().generate(
        make_transaction()
    )

    credit_lines = [
        line
        for line in result.journal.lines
        if line.credit > Decimal("0")
    ]

    assert len(credit_lines) == 1
