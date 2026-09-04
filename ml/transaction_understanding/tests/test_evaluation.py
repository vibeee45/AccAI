import pytest

from ml.transaction_understanding.evaluation.config import (
    EvaluationConfig,
)
from ml.transaction_understanding.evaluation.evaluator import (
    ModelEvaluator,
)
from ml.transaction_understanding.evaluation.inference import (
    EvaluationService,
)
from ml.transaction_understanding.evaluation.metrics import (
    accuracy,
    classification_metrics,
    confidence_metrics,
    f1,
    per_class_metrics,
    precision,
    recall,
    validate_labels,
)
from ml.transaction_understanding.evaluation.schemas import (
    ClassMetrics,
    ClassificationMetrics,
    ConfidenceMetrics,
    EvaluationReport,
)


def test_default_config():
    config = EvaluationConfig()

    assert config.zero_division == 0
    assert config.confidence_bins == 10


def test_custom_config():
    config = EvaluationConfig(
        zero_division=1,
        confidence_bins=5,
    )

    assert config.zero_division == 1
    assert config.confidence_bins == 5


def test_config_rejects_invalid_zero_division():
    with pytest.raises(ValueError):
        EvaluationConfig(zero_division=2)


def test_config_rejects_invalid_bins():
    with pytest.raises(ValueError):
        EvaluationConfig(confidence_bins=0)


def test_validate_labels():
    validate_labels(
        ["sales", "rent"],
        ["sales", "rent"],
    )


def test_validate_labels_rejects_empty_true():
    with pytest.raises(ValueError):
        validate_labels([], ["sales"])


def test_validate_labels_rejects_empty_pred():
    with pytest.raises(ValueError):
        validate_labels(["sales"], [])


def test_validate_labels_rejects_length_mismatch():
    with pytest.raises(ValueError):
        validate_labels(
            ["sales"],
            ["sales", "rent"],
        )


def test_accuracy_perfect():
    assert accuracy(
        ["sales", "rent"],
        ["sales", "rent"],
    ) == pytest.approx(1.0)


def test_accuracy_partial():
    value = accuracy(
        ["sales", "rent", "purchase"],
        ["sales", "sales", "purchase"],
    )

    assert value == pytest.approx(2 / 3)


def test_precision_perfect():
    assert precision(
        ["sales", "rent"],
        ["sales", "rent"],
    ) == pytest.approx(1.0)


def test_recall_perfect():
    assert recall(
        ["sales", "rent"],
        ["sales", "rent"],
    ) == pytest.approx(1.0)


def test_f1_perfect():
    assert f1(
        ["sales", "rent"],
        ["sales", "rent"],
    ) == pytest.approx(1.0)


def test_classification_metrics():
    result = classification_metrics(
        ["sales", "rent", "purchase"],
        ["sales", "sales", "purchase"],
    )

    assert result["support"] == 3
    assert 0.0 <= result["accuracy"] <= 1.0
    assert 0.0 <= result["precision"] <= 1.0
    assert 0.0 <= result["recall"] <= 1.0
    assert 0.0 <= result["f1"] <= 1.0


def test_per_class_metrics():
    result = per_class_metrics(
        ["sales", "rent", "sales"],
        ["sales", "sales", "sales"],
    )

    assert "sales" in result
    assert "rent" in result

    assert result["sales"]["support"] == 2
    assert result["rent"]["support"] == 1


def test_per_class_metrics_contains_f1():
    result = per_class_metrics(
        ["sales", "rent"],
        ["sales", "rent"],
    )

    assert result["sales"]["f1"] == pytest.approx(1.0)
    assert result["rent"]["f1"] == pytest.approx(1.0)


def test_confidence_metrics_perfect():
    result = confidence_metrics(
        ["sales", "rent"],
        ["sales", "rent"],
        [1.0, 1.0],
    )

    assert result["mean_confidence"] == pytest.approx(1.0)
    assert result["accuracy"] == pytest.approx(1.0)
    assert result["calibration_error"] == pytest.approx(0.0)


def test_confidence_metrics_low_confidence():
    result = confidence_metrics(
        ["sales", "rent"],
        ["sales", "rent"],
        [0.5, 0.5],
    )

    assert result["mean_confidence"] == pytest.approx(0.5)
    assert result["accuracy"] == pytest.approx(1.0)
    assert result["calibration_error"] > 0.0


def test_confidence_metrics_requires_matching_length():
    with pytest.raises(ValueError):
        confidence_metrics(
            ["sales", "rent"],
            ["sales", "rent"],
            [0.9],
        )


def test_confidence_metrics_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        confidence_metrics(
            ["sales"],
            ["sales"],
            [1.5],
        )


def test_confidence_metrics_rejects_negative_confidence():
    with pytest.raises(ValueError):
        confidence_metrics(
            ["sales"],
            ["sales"],
            [-0.1],
        )


def test_confidence_metrics_rejects_invalid_bins():
    with pytest.raises(ValueError):
        confidence_metrics(
            ["sales"],
            ["sales"],
            [0.9],
            bins=0,
        )


def test_classification_schema():
    result = ClassificationMetrics(
        accuracy=0.9,
        precision=0.9,
        recall=0.8,
        f1=0.85,
        support=100,
    )

    assert result.accuracy == 0.9
    assert result.support == 100


def test_classification_schema_rejects_invalid_score():
    with pytest.raises(ValueError):
        ClassificationMetrics(
            accuracy=1.5,
            precision=0.9,
            recall=0.8,
            f1=0.85,
            support=100,
        )


def test_classification_schema_rejects_negative_support():
    with pytest.raises(ValueError):
        ClassificationMetrics(
            accuracy=0.9,
            precision=0.9,
            recall=0.8,
            f1=0.85,
            support=-1,
        )


def test_class_metrics_schema():
    result = ClassMetrics(
        label="sales",
        precision=0.9,
        recall=0.8,
        f1=0.85,
        support=10,
    )

    assert result.label == "sales"
    assert result.support == 10


def test_class_metrics_rejects_empty_label():
    with pytest.raises(ValueError):
        ClassMetrics(
            label="",
            precision=0.9,
            recall=0.8,
            f1=0.85,
            support=10,
        )


def test_confidence_schema():
    result = ConfidenceMetrics(
        mean_confidence=0.9,
        accuracy=0.85,
        calibration_error=0.05,
    )

    assert result.mean_confidence == 0.9


def test_confidence_schema_rejects_invalid_mean():
    with pytest.raises(ValueError):
        ConfidenceMetrics(
            mean_confidence=1.2,
            accuracy=0.85,
            calibration_error=0.05,
        )


def test_confidence_schema_rejects_negative_calibration_error():
    with pytest.raises(ValueError):
        ConfidenceMetrics(
            mean_confidence=0.9,
            accuracy=0.85,
            calibration_error=-0.1,
        )


def test_evaluation_report():
    metrics = ClassificationMetrics(
        accuracy=1.0,
        precision=1.0,
        recall=1.0,
        f1=1.0,
        support=2,
    )

    report = EvaluationReport(
        task="classification",
        metrics=metrics,
    )

    assert report.task == "classification"


def test_evaluation_report_rejects_empty_task():
    metrics = ClassificationMetrics(
        accuracy=1.0,
        precision=1.0,
        recall=1.0,
        f1=1.0,
        support=2,
    )

    with pytest.raises(ValueError):
        EvaluationReport(
            task="",
            metrics=metrics,
        )


def test_evaluator_ready():
    assert ModelEvaluator().is_ready() is True


def test_evaluate_classification():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent", "purchase"],
        ["sales", "rent", "purchase"],
    )

    assert isinstance(
        report,
        EvaluationReport,
    )

    assert report.task == "classification"
    assert report.metrics.accuracy == pytest.approx(1.0)
    assert report.metrics.f1 == pytest.approx(1.0)


def test_evaluate_classification_with_confidence():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent"],
        ["sales", "rent"],
        confidences=[0.95, 0.90],
    )

    assert report.confidence_metrics is not None
    assert report.confidence_metrics.mean_confidence == pytest.approx(
        0.925
    )


def test_evaluate_classification_without_confidence():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent"],
        ["sales", "rent"],
    )

    assert report.confidence_metrics is None


def test_evaluate_classification_has_per_class_metrics():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent", "purchase"],
        ["sales", "sales", "purchase"],
    )

    labels = {
        metric.label
        for metric in report.class_metrics
    }

    assert labels == {
        "sales",
        "rent",
        "purchase",
    }


def test_evaluate_account_identification():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_account_identification(
        ["cash", "sales"],
        ["cash", "sales"],
    )

    assert report.task == "account_identification"
    assert report.metrics.accuracy == pytest.approx(1.0)


def test_evaluate_debit_credit():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_debit_credit(
        ["debit", "credit"],
        ["debit", "credit"],
    )

    assert report.task == "debit_credit"
    assert report.metrics.accuracy == pytest.approx(1.0)


def test_evaluate_payment_mode():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_payment_mode(
        ["cash", "upi"],
        ["cash", "upi"],
    )

    assert report.task == "payment_mode"
    assert report.metrics.accuracy == pytest.approx(1.0)


def test_service_classification():
    service = EvaluationService()

    report = service.evaluate_classification(
        ["sales", "rent"],
        ["sales", "rent"],
    )

    assert report.metrics.accuracy == pytest.approx(1.0)


def test_service_account_evaluation():
    service = EvaluationService()

    report = service.evaluate_account_identification(
        ["cash"],
        ["cash"],
    )

    assert report.task == "account_identification"


def test_service_debit_credit_evaluation():
    service = EvaluationService()

    report = service.evaluate_debit_credit(
        ["debit"],
        ["debit"],
    )

    assert report.task == "debit_credit"


def test_service_payment_mode_evaluation():
    service = EvaluationService()

    report = service.evaluate_payment_mode(
        ["upi"],
        ["upi"],
    )

    assert report.task == "payment_mode"


def test_service_ready():
    assert EvaluationService().is_ready() is True


def test_evaluator_custom_config():
    evaluator = ModelEvaluator(
        EvaluationConfig(
            zero_division=1,
            confidence_bins=5,
        )
    )

    assert evaluator.config.confidence_bins == 5


def test_evaluation_support_equals_dataset_size():
    evaluator = ModelEvaluator()

    y_true = [
        "sales",
        "rent",
        "purchase",
        "sales",
    ]

    report = evaluator.evaluate_classification(
        y_true,
        [
            "sales",
            "rent",
            "purchase",
            "rent",
        ],
    )

    assert report.metrics.support == 4


def test_evaluation_detects_imperfect_prediction():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent", "purchase"],
        ["sales", "sales", "purchase"],
    )

    assert report.metrics.accuracy < 1.0
    assert report.metrics.f1 < 1.0


def test_confidence_calibration_error_is_nonnegative():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent", "purchase"],
        ["sales", "sales", "purchase"],
        confidences=[0.9, 0.8, 0.95],
    )

    assert report.confidence_metrics is not None
    assert (
        report.confidence_metrics.calibration_error
        >= 0.0
    )


def test_report_contains_all_class_metrics():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent", "purchase"],
        ["sales", "rent", "purchase"],
    )

    assert len(report.class_metrics) == 3


def test_perfect_model_has_zero_calibration_error():
    evaluator = ModelEvaluator()

    report = evaluator.evaluate_classification(
        ["sales", "rent", "purchase"],
        ["sales", "rent", "purchase"],
        confidences=[1.0, 1.0, 1.0],
    )

    assert report.confidence_metrics is not None
    assert report.confidence_metrics.calibration_error == pytest.approx(
        0.0
    )
