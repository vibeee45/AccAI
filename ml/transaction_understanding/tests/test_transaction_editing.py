from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ml.transaction_understanding.prediction.schemas import (
    PredictionAccount,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionStatus,
    TransactionPrediction,
)
from ml.transaction_understanding.transaction_editing.config import (
    TransactionEditingConfig,
)
from ml.transaction_understanding.transaction_editing.editor import (
    TransactionEditor,
)
from ml.transaction_understanding.transaction_editing.inference import (
    TransactionEditingService,
)
from ml.transaction_understanding.transaction_editing.schemas import (
    EditableTransaction,
    TransactionEdit,
    TransactionEditResult,
)


def make_prediction(
    *,
    amount: float = 5000.0,
) -> TransactionPrediction:
    debit_account = PredictionAccount(
        account_id="rent_expense",
        account_name="Rent Expense",
        confidence=0.95,
    )

    credit_account = PredictionAccount(
        account_id="bank",
        account_name="Bank",
        confidence=0.94,
    )

    debit_prediction = PredictionDirection(
        account_id="rent_expense",
        account_name="Rent Expense",
        direction="debit",
        confidence=0.95,
        reason="Expense account is debited.",
        requires_review=False,
    )

    credit_prediction = PredictionDirection(
        account_id="bank",
        account_name="Bank",
        direction="credit",
        confidence=0.94,
        reason="Bank account is credited.",
        requires_review=False,
    )

    payment_mode = PredictionPaymentMode(
        mode="NEFT",
        confidence=0.92,
        requires_review=False,
    )

    return TransactionPrediction(
        transaction_id="TX-001",
        raw_text="Paid office rent of Rs 5,000 by NEFT.",
        normalized_text="paid office rent of rs 5000 by neft.",
        amount=amount,
        transaction_class="rent",
        classification_confidence=0.96,
        debit_account=debit_account,
        credit_account=credit_account,
        debit_prediction=debit_prediction,
        credit_prediction=credit_prediction,
        payment_mode=payment_mode,
        status=PredictionStatus.SUCCESS,
    )


def test_config_defaults():
    config = TransactionEditingConfig()

    assert config.max_reason_length == 500
    assert config.max_metadata_entries == 100


def test_config_rejects_invalid_values():
    with pytest.raises(ValueError):
        TransactionEditingConfig(
            max_reason_length=0,
        )

    with pytest.raises(ValueError):
        TransactionEditingConfig(
            max_metadata_entries=0,
        )


def test_editable_transaction_schema():
    transaction = EditableTransaction(
        transaction_id="TX-001",
        raw_text="Paid rent.",
        normalized_text="paid rent.",
        amount=1000.0,
        transaction_class="rent",
        debit_account_id="rent_expense",
        debit_account_name="Rent Expense",
        credit_account_id="bank",
        credit_account_name="Bank",
        payment_mode="NEFT",
    )

    assert transaction.transaction_id == "TX-001"
    assert transaction.amount == 1000.0


def test_editable_transaction_rejects_empty_id():
    with pytest.raises(ValueError):
        EditableTransaction(
            transaction_id="",
            raw_text="Paid rent.",
            normalized_text="paid rent.",
            amount=1000.0,
            transaction_class="rent",
            debit_account_id="rent_expense",
            debit_account_name="Rent Expense",
            credit_account_id="bank",
            credit_account_name="Bank",
            payment_mode="NEFT",
        )


def test_editable_transaction_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        EditableTransaction(
            transaction_id="TX-001",
            raw_text="Paid rent.",
            normalized_text="paid rent.",
            amount=0,
            transaction_class="rent",
            debit_account_id="rent_expense",
            debit_account_name="Rent Expense",
            credit_account_id="bank",
            credit_account_name="Bank",
            payment_mode="NEFT",
        )


def test_editable_transaction_rejects_same_accounts():
    with pytest.raises(ValueError):
        EditableTransaction(
            transaction_id="TX-001",
            raw_text="Paid rent.",
            normalized_text="paid rent.",
            amount=1000.0,
            transaction_class="rent",
            debit_account_id="bank",
            debit_account_name="Bank",
            credit_account_id="bank",
            credit_account_name="Bank",
            payment_mode="NEFT",
        )


def test_transaction_edit_schema():
    edit = TransactionEdit(
        field="amount",
        old_value=1000.0,
        new_value=1500.0,
    )

    assert edit.field == "amount"
    assert edit.old_value == 1000.0
    assert edit.new_value == 1500.0


def test_transaction_edit_rejects_unknown_field():
    with pytest.raises(ValueError):
        TransactionEdit(
            field="unknown",
            old_value="a",
            new_value="b",
        )


def test_transaction_edit_rejects_same_value():
    with pytest.raises(ValueError):
        TransactionEdit(
            field="amount",
            old_value=1000.0,
            new_value=1000.0,
        )


def test_snapshot_from_prediction():
    editor = TransactionEditor()

    prediction = make_prediction()

    snapshot = editor.snapshot(prediction)

    assert isinstance(
        snapshot,
        EditableTransaction,
    )

    assert snapshot.transaction_id == "TX-001"
    assert snapshot.amount == 5000.0
    assert snapshot.transaction_class == "rent"
    assert snapshot.debit_account_id == "rent_expense"
    assert snapshot.credit_account_id == "bank"
    assert snapshot.payment_mode == "NEFT"


def test_snapshot_rejects_wrong_type():
    editor = TransactionEditor()

    with pytest.raises(TypeError):
        editor.snapshot("invalid")


def test_snapshot_rejects_missing_amount():
    prediction = make_prediction()
    prediction = TransactionPrediction(
        transaction_id=prediction.transaction_id,
        raw_text=prediction.raw_text,
        normalized_text=prediction.normalized_text,
        amount=None,
        transaction_class=prediction.transaction_class,
        classification_confidence=prediction.classification_confidence,
        debit_account=prediction.debit_account,
        credit_account=prediction.credit_account,
        debit_prediction=prediction.debit_prediction,
        credit_prediction=prediction.credit_prediction,
        payment_mode=prediction.payment_mode,
        status=prediction.status,
    )

    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.snapshot(prediction)


def test_edit_amount():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 6000.0,
        },
        edited_by="reviewer-1",
        reason="Corrected transaction amount.",
    )

    assert result.original.amount == 5000.0
    assert result.edited.amount == 6000.0
    assert result.changed_fields == ("amount",)
    assert result.has_changes is True
    assert result.edited_by == "reviewer-1"


def test_edit_multiple_fields():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 6500.0,
            "payment_mode": "UPI",
            "transaction_class": "utilities",
        },
        edited_by="reviewer-2",
        reason="Corrected transaction classification and payment details.",
    )

    assert result.edited.amount == 6500.0
    assert result.edited.payment_mode == "UPI"
    assert result.edited.transaction_class == "utilities"

    assert set(result.changed_fields) == {
        "amount",
        "payment_mode",
        "transaction_class",
    }

    assert len(result.edits) == 3


def test_edit_account():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "debit_account_id": "utilities_expense",
            "debit_account_name": "Utilities Expense",
        },
        reason="Corrected debit account.",
    )

    assert result.edited.debit_account_id == "utilities_expense"
    assert result.edited.debit_account_name == "Utilities Expense"

    assert result.original.debit_account_id == "rent_expense"


def test_edit_never_mutates_original_prediction():
    editor = TransactionEditor()

    prediction = make_prediction()

    result = editor.edit(
        prediction,
        {
            "amount": 9000.0,
            "payment_mode": "UPI",
        },
    )

    assert prediction.amount == 5000.0
    assert prediction.payment_mode.mode == "NEFT"

    assert result.edited.amount == 9000.0
    assert result.edited.payment_mode == "UPI"


def test_edit_preserves_transaction_identity():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 7500.0,
        },
    )

    assert (
        result.original.transaction_id
        == result.edited.transaction_id
        == "TX-001"
    )


def test_edit_stores_old_and_new_values():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 7000.0,
        },
    )

    edit = result.edits[0]

    assert edit.field == "amount"
    assert edit.old_value == 5000.0
    assert edit.new_value == 7000.0


def test_edit_records_timestamp():
    editor = TransactionEditor()

    timestamp = datetime(
        2026,
        9,
        4,
        20,
        0,
        tzinfo=timezone.utc,
    )

    result = editor.edit(
        make_prediction(),
        {
            "amount": 7000.0,
        },
        edited_at=timestamp,
    )

    assert result.edited_at == timestamp


def test_edit_rejects_naive_timestamp():
    editor = TransactionEditor()

    timestamp = datetime(
        2026,
        9,
        4,
        20,
        0,
    )

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "amount": 7000.0,
            },
            edited_at=timestamp,
        )


def test_edit_rejects_empty_changes():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {},
        )


def test_edit_rejects_unknown_field():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "unknown_field": "value",
            },
        )


def test_edit_rejects_same_value():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "amount": 5000.0,
            },
        )


def test_edit_rejects_invalid_amount():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "amount": 0,
            },
        )


def test_edit_rejects_non_numeric_amount():
    editor = TransactionEditor()

    with pytest.raises(TypeError):
        editor.edit(
            make_prediction(),
            {
                "amount": "7000",
            },
        )


def test_edit_rejects_empty_string_field():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "payment_mode": "",
            },
        )


def test_edit_rejects_invalid_reason():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "amount": 7000.0,
            },
            reason="",
        )


def test_edit_rejects_long_reason():
    editor = TransactionEditor(
        TransactionEditingConfig(
            max_reason_length=10,
        )
    )

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "amount": 7000.0,
            },
            reason="This reason is too long.",
        )


def test_edit_metadata():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 7000.0,
        },
        metadata={
            "source": "review_ui",
            "screen": "transaction_review",
        },
    )

    assert result.metadata["source"] == "review_ui"
    assert result.metadata["screen"] == "transaction_review"


def test_edit_rejects_too_many_metadata_entries():
    editor = TransactionEditor(
        TransactionEditingConfig(
            max_metadata_entries=1,
        )
    )

    with pytest.raises(ValueError):
        editor.edit(
            make_prediction(),
            {
                "amount": 7000.0,
            },
            metadata={
                "a": 1,
                "b": 2,
            },
        )


def test_result_has_changes():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 8000.0,
        },
    )

    assert result.has_changes is True


def test_result_schema_rejects_different_transaction_ids():
    first = EditableTransaction(
        transaction_id="TX-001",
        raw_text="Paid rent.",
        normalized_text="paid rent.",
        amount=1000.0,
        transaction_class="rent",
        debit_account_id="rent_expense",
        debit_account_name="Rent Expense",
        credit_account_id="bank",
        credit_account_name="Bank",
        payment_mode="NEFT",
    )

    second = EditableTransaction(
        transaction_id="TX-002",
        raw_text="Paid rent.",
        normalized_text="paid rent.",
        amount=1500.0,
        transaction_class="rent",
        debit_account_id="rent_expense",
        debit_account_name="Rent Expense",
        credit_account_id="bank",
        credit_account_name="Bank",
        payment_mode="NEFT",
    )

    with pytest.raises(ValueError):
        TransactionEditResult(
            original=first,
            edited=second,
            edits=(),
            edited_at=datetime.now(timezone.utc),
            edited_by=None,
            reason="test",
        )


def test_service_edit():
    service = TransactionEditingService()

    result = service.edit(
        make_prediction(),
        {
            "amount": 5500.0,
        },
        edited_by="reviewer",
        reason="Corrected amount.",
    )

    assert isinstance(
        result,
        TransactionEditResult,
    )

    assert result.edited.amount == 5500.0


def test_service_is_ready():
    service = TransactionEditingService()

    assert service.is_ready() is True


def test_service_rejects_editor_and_config_together():
    editor = TransactionEditor()

    with pytest.raises(ValueError):
        TransactionEditingService(
            editor=editor,
            config=TransactionEditingConfig(),
        )


def test_multiple_edits_keep_order():
    editor = TransactionEditor()

    result = editor.edit(
        make_prediction(),
        {
            "amount": 6000.0,
            "payment_mode": "UPI",
            "transaction_class": "utilities",
        },
    )

    assert [
        edit.field
        for edit in result.edits
    ] == [
        "amount",
        "payment_mode",
        "transaction_class",
    ]
