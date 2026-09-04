from decimal import Decimal

from ml.transaction_understanding.preprocessing import (
    TransactionPreprocessor,
)
from ml.transaction_understanding.prediction import (
    PredictionStatus,
    TransactionPrediction,
    PredictionAccount,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionConfidence,
)
from ml.transaction_understanding.structured_output import (
    StructuredOutputSerializer,
)
from ml.transaction_understanding.accounting_adapter import (
    AccountingTransaction,
    AccountingAccount,
)
from ml.transaction_understanding.debit_credit import (
    DebitCredit,
)
from ml.transaction_understanding.confidence_routing import (
    ConfidenceRouter,
    RoutingDecision,
)
from ml.transaction_understanding.rule_validation import (
    AccountingRuleValidator,
    ValidationStatus,
)
from ml.transaction_understanding.journal_generation import (
    JournalGenerator,
)


def make_accounting_transaction(
    transaction_id="txn-e2e",
    amount=Decimal("5000"),
    transaction_class="sales",
    payment_mode="cash",
    debit_account_id="cash",
    debit_account_name="Cash",
    credit_account_id="sales",
    credit_account_name="Sales",
    ai_confidence=0.97,
    requires_review=False,
    description="Received cash sales",
    source_text="Received cash sales of Rs 5000",
    normalized_text="received cash sales of rs 5000",
):
    return AccountingTransaction(
        transaction_id=transaction_id,
        description=description,
        amount=amount,
        transaction_class=transaction_class,
        payment_mode=payment_mode,
        ai_confidence=ai_confidence,
        requires_review=requires_review,
        source_text=source_text,
        normalized_text=normalized_text,
        debit_account=AccountingAccount(
            account_id=debit_account_id,
            account_name=debit_account_name,
        ),
        credit_account=AccountingAccount(
            account_id=credit_account_id,
            account_name=credit_account_name,
        ),
    )


def journal_totals(journal):
    total_debit = sum(
        (line.debit for line in journal.lines),
        Decimal("0"),
    )

    total_credit = sum(
        (line.credit for line in journal.lines),
        Decimal("0"),
    )

    return total_debit, total_credit


def test_complete_high_confidence_transaction_flow():
    raw_text = "Received cash sales of Rs 5000"

    preprocessor = TransactionPreprocessor()

    processed = preprocessor.preprocess(raw_text)

    assert processed.normalized_text
    assert "5000" in processed.normalized_text


def test_prediction_schema_to_structured_output():
    prediction = TransactionPrediction(
        transaction_id="txn-e2e-001",
        raw_text="Received cash sales of Rs 5000",
        normalized_text="received cash sales of rs 5000",
        amount=Decimal("5000"),
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=PredictionAccount(
            account_id="cash",
            account_name="Cash",
            confidence=0.96,
        ),
        credit_account=PredictionAccount(
            account_id="sales",
            account_name="Sales",
            confidence=0.97,
        ),
        debit_prediction=PredictionDirection(
            account_id="cash",
            account_name="Cash",
            direction=DebitCredit.DEBIT,
            confidence=0.98,
            reason="Cash received increases the cash account.",
            requires_review=False,
        ),
        credit_prediction=PredictionDirection(
            account_id="sales",
            account_name="Sales",
            direction=DebitCredit.CREDIT,
            confidence=0.98,
            reason="Sales income is credited.",
            requires_review=False,
        ),
        payment_mode=PredictionPaymentMode(
            mode="cash",
            confidence=0.99,
            requires_review=False,
        ),
        confidence=PredictionConfidence(
            overall=0.97,
            requires_review=False,
            reason="High confidence prediction.",
        ),
        status=PredictionStatus.SUCCESS,
    )

    structured = StructuredOutputSerializer().serialize(
        prediction
    )

    assert structured.transaction_id == "txn-e2e-001"
    assert structured.amount == Decimal("5000")
    assert structured.transaction_class == "sales"
    assert structured.debit_account.account_id == "cash"
    assert structured.credit_account.account_id == "sales"


def test_prediction_to_accounting_adapter():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-002",
    )

    assert transaction.debit_account.account_id == "cash"
    assert transaction.credit_account.account_id == "sales"
    assert transaction.amount == Decimal("5000")
    assert transaction.ai_confidence == 0.97
    assert transaction.requires_review is False


def test_high_confidence_routes_to_automatic_processing():
    result = ConfidenceRouter().route(
        0.97,
        requires_review=False,
    )

    assert result.decision == RoutingDecision.AUTO_PROCESS
    assert result.requires_review is False


def test_medium_confidence_routes_to_human_review():
    result = ConfidenceRouter().route(
        0.65,
        requires_review=False,
    )

    assert result.decision == RoutingDecision.HUMAN_REVIEW
    assert result.requires_review is True


def test_low_confidence_routes_to_rejection():
    result = ConfidenceRouter().route(
        0.30,
        requires_review=False,
    )

    assert result.decision == RoutingDecision.REJECT


def test_explicit_review_overrides_high_confidence():
    result = ConfidenceRouter().route(
        0.98,
        requires_review=True,
    )

    assert result.decision == RoutingDecision.HUMAN_REVIEW
    assert result.requires_review is True


def test_rule_validation_accepts_valid_accounting_transaction():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-003",
        ai_confidence=0.97,
        requires_review=False,
    )

    result = AccountingRuleValidator().validate(
        transaction
    )

    assert result.valid is True
    assert result.status == ValidationStatus.VALID


def test_rule_validation_requires_review_for_low_confidence():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-004",
        ai_confidence=0.65,
        requires_review=False,
    )

    result = AccountingRuleValidator().validate(
        transaction
    )

    assert result.valid is True
    assert result.status == ValidationStatus.REVIEW_REQUIRED


def test_validated_transaction_generates_balanced_journal():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-005",
        ai_confidence=0.97,
    )

    validation = AccountingRuleValidator().validate(
        transaction
    )

    assert validation.valid is True
    assert validation.status == ValidationStatus.VALID

    result = JournalGenerator().generate(
        transaction
    )

    assert result.success is True
    assert result.journal is not None

    journal = result.journal

    total_debit, total_credit = journal_totals(
        journal
    )

    assert journal.amount == Decimal("5000")
    assert total_debit == Decimal("5000")
    assert total_credit == Decimal("5000")
    assert total_debit == total_credit


def test_journal_contains_correct_debit_account():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-006",
    )

    result = JournalGenerator().generate(
        transaction
    )

    assert result.success is True
    assert result.journal is not None

    journal = result.journal

    debit_lines = [
        line
        for line in journal.lines
        if line.debit > Decimal("0")
    ]

    assert len(debit_lines) == 1
    assert debit_lines[0].account_id == "cash"
    assert debit_lines[0].debit == Decimal("5000")
    assert debit_lines[0].credit == Decimal("0")


def test_journal_contains_correct_credit_account():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-007",
    )

    result = JournalGenerator().generate(
        transaction
    )

    assert result.success is True
    assert result.journal is not None

    journal = result.journal

    credit_lines = [
        line
        for line in journal.lines
        if line.credit > Decimal("0")
    ]

    assert len(credit_lines) == 1
    assert credit_lines[0].account_id == "sales"
    assert credit_lines[0].credit == Decimal("5000")
    assert credit_lines[0].debit == Decimal("0")


def test_end_to_end_pipeline_blocks_failed_transaction():
    result = ConfidenceRouter().route(
        0.95,
        failed=True,
        retryable=False,
    )

    assert result.decision == RoutingDecision.REJECT
    assert result.requires_review is True


def test_end_to_end_pipeline_does_not_generate_unvalidated_entry():
    transaction = make_accounting_transaction(
        transaction_id="txn-e2e-008",
        ai_confidence=0.40,
        requires_review=False,
    )

    routing = ConfidenceRouter().route(
        transaction.ai_confidence
    )

    assert routing.decision == RoutingDecision.REJECT

    validation = AccountingRuleValidator().validate(
        transaction
    )

    assert validation.valid is True
    assert routing.decision != RoutingDecision.AUTO_PROCESS


def test_complete_pipeline_preserves_transaction_identity():
    transaction = make_accounting_transaction(
        transaction_id="txn-final-001",
        amount=Decimal("12500"),
        transaction_class="sales",
        payment_mode="upi",
        debit_account_id="bank",
        debit_account_name="Bank",
        credit_account_id="sales",
        credit_account_name="Sales",
        ai_confidence=0.94,
        description="Received sales payment through UPI",
        source_text=(
            "Received sales payment through UPI Rs 12500"
        ),
        normalized_text=(
            "received sales payment through upi rs 12500"
        ),
    )

    routing = ConfidenceRouter().route(
        transaction.ai_confidence
    )

    assert routing.decision == RoutingDecision.AUTO_PROCESS

    validation = AccountingRuleValidator().validate(
        transaction
    )

    assert validation.valid is True

    journal_result = JournalGenerator().generate(
        transaction
    )

    assert journal_result.success is True
    assert journal_result.journal is not None

    journal = journal_result.journal

    total_debit, total_credit = journal_totals(
        journal
    )

    assert journal.transaction_id == "txn-final-001"
    assert journal.journal_id == "JE-txn-final-001"
    assert journal.amount == Decimal("12500")
    assert total_debit == total_credit
    assert total_debit == Decimal("12500")