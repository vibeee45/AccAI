import pytest

from ml.transaction_understanding.prediction import (
    PredictionAccount,
    PredictionBatch,
    PredictionConfidence,
    PredictionDirection,
    PredictionPaymentMode,
    PredictionSemanticMatch,
    PredictionStatus,
    TransactionPrediction,
)


def make_account(
    account_id="cash",
    account_name="Cash",
    confidence=0.95,
):
    return PredictionAccount(
        account_id=account_id,
        account_name=account_name,
        confidence=confidence,
    )


def make_direction(
    account_id="cash",
    account_name="Cash",
    direction="debit",
    confidence=0.95,
):
    return PredictionDirection(
        account_id=account_id,
        account_name=account_name,
        direction=direction,
        confidence=confidence,
        reason="Explicit accounting rule.",
        requires_review=False,
    )


def make_payment_mode():
    return PredictionPaymentMode(
        mode="cash",
        confidence=0.98,
        requires_review=False,
    )


def make_prediction(
    transaction_id="txn-001",
):
    return TransactionPrediction(
        transaction_id=transaction_id,
        raw_text="received cash from customer",
        normalized_text=(
            "received cash from customer"
        ),
        amount=1000.0,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=make_account(
            "cash",
            "Cash",
        ),
        credit_account=make_account(
            "sales",
            "Sales",
        ),
        debit_prediction=make_direction(
            "cash",
            "Cash",
            "debit",
        ),
        credit_prediction=make_direction(
            "sales",
            "Sales",
            "credit",
        ),
        payment_mode=make_payment_mode(),
    )


def test_prediction_status_values():
    assert PredictionStatus.SUCCESS.value == "success"
    assert (
        PredictionStatus.REVIEW_REQUIRED.value
        == "review_required"
    )
    assert PredictionStatus.FAILED.value == "failed"


def test_prediction_account():
    account = make_account()

    assert account.account_id == "cash"
    assert account.account_name == "Cash"
    assert account.confidence == 0.95


@pytest.mark.parametrize(
    "confidence",
    [-0.1, 1.1],
)
def test_prediction_account_rejects_invalid_confidence(
    confidence,
):
    with pytest.raises(ValueError):
        make_account(
            confidence=confidence
        )


def test_prediction_account_rejects_empty_id():
    with pytest.raises(ValueError):
        make_account(account_id="")


def test_prediction_account_rejects_empty_name():
    with pytest.raises(ValueError):
        make_account(account_name="")


def test_prediction_direction():
    direction = make_direction()

    assert direction.direction == "debit"
    assert direction.requires_review is False


def test_prediction_direction_allows_credit():
    direction = make_direction(
        direction="credit"
    )

    assert direction.direction == "credit"


def test_prediction_direction_rejects_invalid_direction():
    with pytest.raises(ValueError):
        make_direction(
            direction="invalid"
        )


def test_prediction_direction_rejects_empty_reason():
    with pytest.raises(ValueError):
        PredictionDirection(
            account_id="cash",
            account_name="Cash",
            direction="debit",
            confidence=0.9,
            reason="",
            requires_review=False,
        )


def test_payment_mode():
    payment = make_payment_mode()

    assert payment.mode == "cash"
    assert payment.confidence == 0.98


def test_payment_mode_rejects_empty_mode():
    with pytest.raises(ValueError):
        PredictionPaymentMode(
            mode="",
            confidence=0.9,
            requires_review=False,
        )


def test_semantic_match():
    match = PredictionSemanticMatch(
        candidate_id="candidate-1",
        candidate_text="cash received",
        similarity=0.91,
    )

    assert match.candidate_id == "candidate-1"
    assert match.similarity == 0.91


def test_semantic_match_rejects_invalid_similarity():
    with pytest.raises(ValueError):
        PredictionSemanticMatch(
            candidate_id="candidate-1",
            candidate_text="cash",
            similarity=1.5,
        )


def test_confidence():
    confidence = PredictionConfidence(
        overall=0.92,
        requires_review=False,
        reason="High confidence prediction.",
    )

    assert confidence.overall == 0.92
    assert confidence.requires_review is False


def test_confidence_rejects_invalid_value():
    with pytest.raises(ValueError):
        PredictionConfidence(
            overall=-0.1,
            requires_review=True,
            reason="Low confidence.",
        )


def test_transaction_prediction():
    prediction = make_prediction()

    assert prediction.transaction_id == "txn-001"
    assert prediction.amount == 1000.0
    assert prediction.transaction_class == "sales"
    assert prediction.status == PredictionStatus.SUCCESS


def test_transaction_prediction_without_amount():
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
    )

    assert prediction.amount is None


def test_transaction_prediction_with_confidence():
    prediction = TransactionPrediction(
        transaction_id="txn-002",
        raw_text="paid rent by bank",
        normalized_text="paid rent by bank",
        amount=5000,
        transaction_class="rent",
        classification_confidence=0.94,
        debit_account=make_account(
            "rent_expense",
            "Rent Expense",
        ),
        credit_account=make_account(
            "bank",
            "Bank",
        ),
        debit_prediction=make_direction(
            "rent_expense",
            "Rent Expense",
            "debit",
        ),
        credit_prediction=make_direction(
            "bank",
            "Bank",
            "credit",
        ),
        payment_mode=PredictionPaymentMode(
            mode="bank_transfer",
            confidence=0.97,
            requires_review=False,
        ),
        confidence=PredictionConfidence(
            overall=0.93,
            requires_review=False,
            reason="High confidence prediction.",
        ),
    )

    assert prediction.confidence.overall == 0.93


def test_transaction_prediction_with_semantic_matches():
    match = PredictionSemanticMatch(
        candidate_id="sales-001",
        candidate_text="cash sale",
        similarity=0.90,
    )

    prediction = TransactionPrediction(
        transaction_id="txn-003",
        raw_text="cash sale",
        normalized_text="cash sale",
        amount=1000,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=make_account(
            "cash",
            "Cash",
        ),
        credit_account=make_account(
            "sales",
            "Sales",
        ),
        debit_prediction=make_direction(
            "cash",
            "Cash",
            "debit",
        ),
        credit_prediction=make_direction(
            "sales",
            "Sales",
            "credit",
        ),
        payment_mode=make_payment_mode(),
        semantic_matches=(match,),
    )

    assert len(
        prediction.semantic_matches
    ) == 1


def test_transaction_prediction_with_entities():
    prediction = TransactionPrediction(
        transaction_id="txn-004",
        raw_text="received 1000 from Rahul",
        normalized_text=(
            "received 1000 from rahul"
        ),
        amount=1000,
        transaction_class="sales",
        classification_confidence=0.90,
        debit_account=make_account(
            "cash",
            "Cash",
        ),
        credit_account=make_account(
            "sales",
            "Sales",
        ),
        debit_prediction=make_direction(
            "cash",
            "Cash",
            "debit",
        ),
        credit_prediction=make_direction(
            "sales",
            "Sales",
            "credit",
        ),
        payment_mode=make_payment_mode(),
        entities=("Rahul",),
    )

    assert prediction.entities == ("Rahul",)


def test_transaction_prediction_with_metadata():
    prediction = TransactionPrediction(
        transaction_id="txn-005",
        raw_text="cash sale",
        normalized_text="cash sale",
        amount=1000,
        transaction_class="sales",
        classification_confidence=0.95,
        debit_account=make_account(
            "cash",
            "Cash",
        ),
        credit_account=make_account(
            "sales",
            "Sales",
        ),
        debit_prediction=make_direction(
            "cash",
            "Cash",
            "debit",
        ),
        credit_prediction=make_direction(
            "sales",
            "Sales",
            "credit",
        ),
        payment_mode=make_payment_mode(),
        metadata={
            "source": "excel",
            "row_number": 10,
        },
    )

    assert prediction.metadata["source"] == "excel"
    assert prediction.metadata["row_number"] == 10


def test_transaction_prediction_rejects_empty_id():
    with pytest.raises(ValueError):
        prediction = make_prediction()

        TransactionPrediction(
            transaction_id="",
            raw_text=prediction.raw_text,
            normalized_text=prediction.normalized_text,
            amount=prediction.amount,
            transaction_class=prediction.transaction_class,
            classification_confidence=prediction.classification_confidence,
            debit_account=prediction.debit_account,
            credit_account=prediction.credit_account,
            debit_prediction=prediction.debit_prediction,
            credit_prediction=prediction.credit_prediction,
            payment_mode=prediction.payment_mode,
        )


def test_transaction_prediction_rejects_negative_amount():
    prediction = make_prediction()

    with pytest.raises(ValueError):
        TransactionPrediction(
            transaction_id="txn-negative",
            raw_text=prediction.raw_text,
            normalized_text=prediction.normalized_text,
            amount=-100,
            transaction_class=prediction.transaction_class,
            classification_confidence=prediction.classification_confidence,
            debit_account=prediction.debit_account,
            credit_account=prediction.credit_account,
            debit_prediction=prediction.debit_prediction,
            credit_prediction=prediction.credit_prediction,
            payment_mode=prediction.payment_mode,
        )


def test_transaction_prediction_rejects_same_accounts():
    with pytest.raises(ValueError):
        TransactionPrediction(
            transaction_id="txn-same",
            raw_text="cash transaction",
            normalized_text="cash transaction",
            amount=100,
            transaction_class="miscellaneous",
            classification_confidence=0.9,
            debit_account=make_account(
                "cash",
                "Cash",
            ),
            credit_account=make_account(
                "cash",
                "Cash",
            ),
            debit_prediction=make_direction(
                "cash",
                "Cash",
                "debit",
            ),
            credit_prediction=make_direction(
                "cash",
                "Cash",
                "credit",
            ),
            payment_mode=make_payment_mode(),
        )


def test_debit_prediction_must_be_debit():
    with pytest.raises(ValueError):
        prediction = make_prediction()

        TransactionPrediction(
            transaction_id="txn-invalid",
            raw_text=prediction.raw_text,
            normalized_text=prediction.normalized_text,
            amount=prediction.amount,
            transaction_class=prediction.transaction_class,
            classification_confidence=prediction.classification_confidence,
            debit_account=prediction.debit_account,
            credit_account=prediction.credit_account,
            debit_prediction=make_direction(
                "cash",
                "Cash",
                "credit",
            ),
            credit_prediction=prediction.credit_prediction,
            payment_mode=prediction.payment_mode,
        )


def test_credit_prediction_must_be_credit():
    with pytest.raises(ValueError):
        prediction = make_prediction()

        TransactionPrediction(
            transaction_id="txn-invalid",
            raw_text=prediction.raw_text,
            normalized_text=prediction.normalized_text,
            amount=prediction.amount,
            transaction_class=prediction.transaction_class,
            classification_confidence=prediction.classification_confidence,
            debit_account=prediction.debit_account,
            credit_account=prediction.credit_account,
            debit_prediction=prediction.debit_prediction,
            credit_prediction=make_direction(
                "sales",
                "Sales",
                "debit",
            ),
            payment_mode=prediction.payment_mode,
        )


def test_prediction_batch():
    first = make_prediction("txn-001")
    second = make_prediction("txn-002")

    batch = PredictionBatch(
        predictions=(first, second)
    )

    assert batch.count == 2
    assert batch.review_required_count == 0
    assert batch.failed_count == 0


def test_prediction_batch_duplicate_ids_rejected():
    first = make_prediction("txn-001")
    second = make_prediction("txn-001")

    with pytest.raises(ValueError):
        PredictionBatch(
            predictions=(first, second)
        )


def test_review_required_count():
    prediction = TransactionPrediction(
        transaction_id="txn-review",
        raw_text="unclear transaction",
        normalized_text="unclear transaction",
        amount=100,
        transaction_class="miscellaneous",
        classification_confidence=0.5,
        debit_account=make_account(
            "cash",
            "Cash",
            0.5,
        ),
        credit_account=make_account(
            "sales",
            "Sales",
            0.5,
        ),
        debit_prediction=PredictionDirection(
            account_id="cash",
            account_name="Cash",
            direction="debit",
            confidence=0.5,
            reason="Low confidence; human review required.",
            requires_review=True,
        ),
        credit_prediction=PredictionDirection(
            account_id="sales",
            account_name="Sales",
            direction="credit",
            confidence=0.5,
            reason="Low confidence; human review required.",
            requires_review=True,
        ),
        payment_mode=PredictionPaymentMode(
            mode="unknown",
            confidence=0.5,
            requires_review=True,
        ),
        status=PredictionStatus.REVIEW_REQUIRED,
    )

    batch = PredictionBatch(
        predictions=(prediction,)
    )

    assert batch.review_required_count == 1


def test_failed_count():
    prediction = make_prediction()

    failed_prediction = TransactionPrediction(
        transaction_id="txn-failed",
        raw_text=prediction.raw_text,
        normalized_text=prediction.normalized_text,
        amount=prediction.amount,
        transaction_class=prediction.transaction_class,
        classification_confidence=prediction.classification_confidence,
        debit_account=prediction.debit_account,
        credit_account=prediction.credit_account,
        debit_prediction=prediction.debit_prediction,
        credit_prediction=prediction.credit_prediction,
        payment_mode=prediction.payment_mode,
        status=PredictionStatus.FAILED,
    )

    batch = PredictionBatch(
        predictions=(failed_prediction,)
    )

    assert batch.failed_count == 1


def test_prediction_is_immutable():
    prediction = make_prediction()

    with pytest.raises(
        AttributeError
    ):
        prediction.amount = 5000


def test_batch_is_immutable():
    prediction = make_prediction()

    batch = PredictionBatch(
        predictions=(prediction,)
    )

    with pytest.raises(
        AttributeError
    ):
        batch.predictions = ()


def test_prediction_defaults():
    prediction = make_prediction()

    assert prediction.confidence is None
    assert prediction.semantic_matches == ()
    assert prediction.entities == ()
    assert prediction.metadata == {}
    assert prediction.status == PredictionStatus.SUCCESS


def test_prediction_account_is_immutable():
    account = make_account()

    with pytest.raises(
        AttributeError
    ):
        account.confidence = 0.5


def test_confidence_is_immutable():
    confidence = PredictionConfidence(
        overall=0.9,
        requires_review=False,
        reason="High confidence.",
    )

    with pytest.raises(
        AttributeError
    ):
        confidence.overall = 0.5


def test_payment_mode_is_immutable():
    payment = make_payment_mode()

    with pytest.raises(
        AttributeError
    ):
        payment.mode = "upi"
