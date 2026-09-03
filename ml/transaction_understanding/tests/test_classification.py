import pytest

from ml.transaction_understanding.classification import (
    ClassificationConfig,
    ClassificationDataset,
    TransactionClassifier,
    TransactionClassificationService,
    TransactionTextFeatures,
)


TRAINING_DATA = [
    ("sold goods to customer for rs 5000", "sales"),
    ("cash sales of products rs 8000", "sales"),
    ("goods sold to ABC Ltd rs 12000", "sales"),

    ("purchased inventory for rs 7000", "purchase"),
    ("bought goods from supplier rs 9000", "purchase"),
    ("inventory purchase through bank rs 11000", "purchase"),

    ("paid office rent rs 25000", "rent"),
    ("monthly shop rent paid rs 18000", "rent"),
    ("rent expense through bank rs 22000", "rent"),

    ("paid employee salary rs 40000", "salary"),
    ("staff wages paid rs 35000", "salary"),
    ("monthly salary transferred rs 50000", "salary"),

    ("electricity bill paid rs 5000", "utilities"),
    ("paid electricity charges rs 4500", "utilities"),
    ("water bill payment rs 2000", "utilities"),

    ("paid transport charges rs 3000", "transport"),
    ("freight expense paid rs 6000", "transport"),
    ("delivery charges rs 2500", "transport"),

    ("advertising expense paid rs 10000", "advertising"),
    ("facebook advertising payment rs 7000", "advertising"),
    ("marketing campaign expense rs 12000", "advertising"),

    ("commission received rs 5000", "commission"),
    ("commission income received through bank rs 8000", "commission"),
    ("paid sales commission rs 4000", "commission"),

    ("interest received rs 3000", "interest"),
    ("bank interest income rs 2500", "interest"),
    ("interest payment rs 2000", "interest"),

    ("cash deposited into bank rs 10000", "cash_deposit"),
    ("deposited cash at bank rs 15000", "cash_deposit"),
    ("cash deposit rs 5000", "cash_deposit"),

    ("cash withdrawn from bank rs 8000", "cash_withdrawal"),
    ("withdrew cash from bank rs 6000", "cash_withdrawal"),
    ("bank cash withdrawal rs 4000", "cash_withdrawal"),

    ("transferred money to bank rs 12000", "bank_transfer"),
    ("bank transfer payment rs 7000", "bank_transfer"),
    ("amount transferred through bank rs 9000", "bank_transfer"),

    ("owner introduced capital rs 100000", "capital_introduction"),
    ("capital introduced by proprietor rs 80000", "capital_introduction"),
    ("owner invested capital rs 120000", "capital_introduction"),

    ("loan received from bank rs 200000", "loan"),
    ("bank loan obtained rs 150000", "loan"),
    ("loan amount received rs 100000", "loan"),

    ("purchased machinery rs 75000", "asset_purchase"),
    ("bought office equipment rs 50000", "asset_purchase"),
    ("purchased computer for business rs 60000", "asset_purchase"),

    ("sold old machinery rs 30000", "asset_sale"),
    ("office equipment sold rs 20000", "asset_sale"),
    ("sold fixed asset for rs 25000", "asset_sale"),

    ("income tax paid rs 15000", "tax"),
    ("paid GST tax rs 12000", "tax"),
    ("tax expense payment rs 8000", "tax"),

    ("insurance premium paid rs 10000", "insurance"),
    ("business insurance payment rs 12000", "insurance"),
    ("insurance expense rs 9000", "insurance"),

    ("dividend income received rs 5000", "miscellaneous_income"),
    ("other income received rs 3000", "miscellaneous_income"),
    ("miscellaneous income rs 4000", "miscellaneous_income"),

    ("office cleaning expense rs 3000", "miscellaneous_expense"),
    ("miscellaneous expense paid rs 2000", "miscellaneous_expense"),
    ("other business expense rs 3500", "miscellaneous_expense"),
]


def create_dataset():
    return ClassificationDataset.from_pairs(
        TRAINING_DATA
    )


def create_classifier():
    config = ClassificationConfig(
        classes=tuple(
            sorted(
                set(
                    label
                    for _, label in TRAINING_DATA
                )
            )
        ),
        confidence_threshold=0.70,
    )

    classifier = TransactionClassifier(config)
    classifier.fit(create_dataset())

    return classifier


def test_config_has_transaction_classes():
    config = ClassificationConfig()

    assert len(config.classes) >= 20
    assert "sales" in config.classes
    assert "purchase" in config.classes
    assert "rent" in config.classes


def test_config_rejects_duplicate_classes():
    with pytest.raises(ValueError):
        ClassificationConfig(
            classes=("sales", "sales")
        )


def test_config_rejects_invalid_test_size():
    with pytest.raises(ValueError):
        ClassificationConfig(
            test_size=1.0
        )


def test_dataset_creation():
    dataset = create_dataset()

    assert len(dataset) == len(TRAINING_DATA)
    assert len(dataset.texts) == len(TRAINING_DATA)
    assert len(dataset.labels) == len(TRAINING_DATA)


def test_dataset_classes():
    dataset = create_dataset()

    assert "sales" in dataset.classes
    assert "rent" in dataset.classes
    assert "salary" in dataset.classes


def test_dataset_class_counts():
    dataset = create_dataset()

    counts = dataset.class_counts()

    assert counts["sales"] == 3
    assert counts["rent"] == 3
    assert counts["salary"] == 3


def test_dataset_rejects_empty():
    with pytest.raises(ValueError):
        ClassificationDataset([])


def test_dataset_rejects_empty_text():
    from ml.transaction_understanding.classification.schemas import (
        ClassificationRecord,
    )

    with pytest.raises(ValueError):
        ClassificationRecord(
            text="",
            label="sales",
        )


def test_dataset_validates_classes():
    dataset = create_dataset()

    dataset.validate_classes(
        (
            "sales",
            "purchase",
            "rent",
            "salary",
            "utilities",
            "transport",
            "advertising",
            "commission",
            "interest",
            "cash_deposit",
            "cash_withdrawal",
            "bank_transfer",
            "capital_introduction",
            "loan",
            "asset_purchase",
            "asset_sale",
            "tax",
            "insurance",
            "miscellaneous_income",
            "miscellaneous_expense",
        )
    )


def test_dataset_rejects_unknown_class():
    dataset = ClassificationDataset.from_pairs(
        [
            ("test transaction", "unknown_class")
        ]
    )

    with pytest.raises(ValueError):
        dataset.validate_classes(
            ("sales", "purchase")
        )


def test_feature_extractor_fit():
    features = TransactionTextFeatures()

    features.fit(
        [
            "paid rent",
            "sold goods",
            "salary paid",
        ]
    )

    assert features.fitted
    assert features.vocabulary_size() > 0


def test_feature_extractor_transform():
    features = TransactionTextFeatures()

    features.fit(
        [
            "paid rent",
            "sold goods",
            "salary paid",
        ]
    )

    matrix = features.transform(
        ["paid office rent"]
    )

    assert matrix.shape[0] == 1
    assert matrix.shape[1] == features.vocabulary_size()


def test_feature_extractor_requires_fit():
    features = TransactionTextFeatures()

    with pytest.raises(RuntimeError):
        features.transform(
            ["paid rent"]
        )


def test_classifier_fits():
    classifier = create_classifier()

    assert classifier.fitted
    assert len(classifier.classes) >= 2
    assert classifier.vocabulary_size() > 0


def test_classifier_predict_sales():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "sold goods to customer rs 15000"
    )

    assert prediction.label == "sales"
    assert 0 <= prediction.confidence <= 1
    assert prediction.probabilities


def test_classifier_predict_rent():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "paid monthly office rent rs 30000"
    )

    assert prediction.label == "rent"


def test_classifier_predict_salary():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "employee salary paid rs 45000"
    )

    assert prediction.label == "salary"


def test_classifier_predict_purchase():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "bought inventory from supplier rs 9000"
    )

    assert prediction.label == "purchase"


def test_classifier_batch_prediction():
    classifier = create_classifier()

    predictions = classifier.predict(
        [
            "sold products rs 5000",
            "paid office rent rs 20000",
            "employee salary paid rs 30000",
        ]
    )

    assert len(predictions) == 3
    assert all(
        prediction.label
        for prediction in predictions
    )


def test_probabilities_sum_to_one():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "paid electricity bill rs 5000"
    )

    total = sum(
        prediction.probabilities.values()
    )

    assert total == pytest.approx(1.0)


def test_confidence_is_max_probability():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "paid office rent rs 25000"
    )

    assert prediction.confidence == pytest.approx(
        max(
            prediction.probabilities.values()
        )
    )


def test_requires_review_is_boolean():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "business transaction"
    )

    assert isinstance(
        prediction.requires_review,
        bool,
    )


def test_classifier_requires_fit():
    classifier = TransactionClassifier()

    with pytest.raises(RuntimeError):
        classifier.predict_one(
            "paid rent"
        )


def test_classifier_rejects_empty_prediction_input():
    classifier = create_classifier()

    with pytest.raises(ValueError):
        classifier.predict([])


def test_classifier_evaluation():
    classifier = create_classifier()

    metrics = classifier.evaluate(
        create_dataset()
    )

    assert metrics.sample_count == len(
        TRAINING_DATA
    )

    assert 0 <= metrics.accuracy <= 1
    assert 0 <= metrics.precision_macro <= 1
    assert 0 <= metrics.recall_macro <= 1
    assert 0 <= metrics.f1_macro <= 1


def test_service_not_ready_before_training():
    service = TransactionClassificationService()

    assert service.ready is False


def test_service_classify_after_training():
    classifier = create_classifier()

    service = TransactionClassificationService(
        classifier
    )

    assert service.ready is True

    prediction = service.classify(
        "paid office rent rs 25000"
    )

    assert prediction.label == "rent"


def test_service_rejects_empty_text():
    classifier = create_classifier()

    service = TransactionClassificationService(
        classifier
    )

    with pytest.raises(ValueError):
        service.classify("")


def test_service_batch_classification():
    classifier = create_classifier()

    service = TransactionClassificationService(
        classifier
    )

    predictions = service.classify_many(
        [
            "sold goods rs 5000",
            "paid rent rs 20000",
        ]
    )

    assert len(predictions) == 2


def test_prediction_schema():
    classifier = create_classifier()

    prediction = classifier.predict_one(
        "cash deposited into bank rs 5000"
    )

    assert prediction.label
    assert isinstance(
        prediction.confidence,
        float,
    )
    assert isinstance(
        prediction.probabilities,
        dict,
    )


def test_metrics_schema():
    from ml.transaction_understanding.classification.schemas import (
        ClassificationMetrics,
    )

    metrics = ClassificationMetrics(
        accuracy=0.9,
        precision_macro=0.88,
        recall_macro=0.87,
        f1_macro=0.875,
        sample_count=100,
    )

    assert metrics.accuracy == 0.9
    assert metrics.sample_count == 100
