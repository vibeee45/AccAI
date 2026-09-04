from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)


def validate_labels(
    y_true: Sequence[str],
    y_pred: Sequence[str],
) -> None:
    if not y_true:
        raise ValueError(
            "y_true cannot be empty."
        )

    if not y_pred:
        raise ValueError(
            "y_pred cannot be empty."
        )

    if len(y_true) != len(y_pred):
        raise ValueError(
            "y_true and y_pred must have the same length."
        )


def accuracy(
    y_true: Sequence[str],
    y_pred: Sequence[str],
) -> float:
    validate_labels(y_true, y_pred)

    return float(
        accuracy_score(y_true, y_pred)
    )


def precision(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    zero_division: int = 0,
) -> float:
    validate_labels(y_true, y_pred)

    return float(
        precision_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=zero_division,
        )
    )


def recall(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    zero_division: int = 0,
) -> float:
    validate_labels(y_true, y_pred)

    return float(
        recall_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=zero_division,
        )
    )


def f1(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    zero_division: int = 0,
) -> float:
    validate_labels(y_true, y_pred)

    return float(
        f1_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=zero_division,
        )
    )


def classification_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    zero_division: int = 0,
):
    validate_labels(y_true, y_pred)

    return {
        "accuracy": accuracy(y_true, y_pred),
        "precision": precision(
            y_true,
            y_pred,
            zero_division=zero_division,
        ),
        "recall": recall(
            y_true,
            y_pred,
            zero_division=zero_division,
        ),
        "f1": f1(
            y_true,
            y_pred,
            zero_division=zero_division,
        ),
        "support": len(y_true),
    }


def per_class_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    zero_division: int = 0,
) -> dict[str, dict[str, float | int]]:
    validate_labels(y_true, y_pred)

    labels = sorted(
        set(y_true) | set(y_pred)
    )

    precisions = precision_score(
        y_true,
        y_pred,
        labels=labels,
        average=None,
        zero_division=zero_division,
    )

    recalls = recall_score(
        y_true,
        y_pred,
        labels=labels,
        average=None,
        zero_division=zero_division,
    )

    f1_scores = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average=None,
        zero_division=zero_division,
    )

    supports = np.bincount(
        [
            labels.index(value)
            for value in y_true
        ],
        minlength=len(labels),
    )

    return {
        label: {
            "precision": float(precisions[index]),
            "recall": float(recalls[index]),
            "f1": float(f1_scores[index]),
            "support": int(supports[index]),
        }
        for index, label in enumerate(labels)
    }


def confidence_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    confidences: Sequence[float],
    *,
    bins: int = 10,
) -> dict[str, float]:
    validate_labels(y_true, y_pred)

    if len(confidences) != len(y_true):
        raise ValueError(
            "confidences must have the same length as labels."
        )

    if bins <= 0:
        raise ValueError(
            "bins must be greater than zero."
        )

    if any(
        not 0.0 <= float(value) <= 1.0
        for value in confidences
    ):
        raise ValueError(
            "All confidence values must be between 0 and 1."
        )

    confidences_array = np.asarray(
        confidences,
        dtype=float,
    )

    correct = np.asarray(
        [
            actual == predicted
            for actual, predicted in zip(
                y_true,
                y_pred,
            )
        ],
        dtype=float,
    )

    mean_confidence = float(
        np.mean(confidences_array)
    )

    accuracy_value = float(
        np.mean(correct)
    )

    bin_edges = np.linspace(
        0.0,
        1.0,
        bins + 1,
    )

    calibration_error = 0.0

    for index in range(bins):
        lower = bin_edges[index]
        upper = bin_edges[index + 1]

        if index == bins - 1:
            mask = (
                (confidences_array >= lower)
                & (confidences_array <= upper)
            )
        else:
            mask = (
                (confidences_array >= lower)
                & (confidences_array < upper)
            )

        if not np.any(mask):
            continue

        bin_accuracy = float(
            np.mean(correct[mask])
        )

        bin_confidence = float(
            np.mean(confidences_array[mask])
        )

        weight = float(
            np.mean(mask)
        )

        calibration_error += (
            weight
            * abs(
                bin_accuracy
                - bin_confidence
            )
        )

    return {
        "mean_confidence": mean_confidence,
        "accuracy": accuracy_value,
        "calibration_error": float(
            calibration_error
        ),
    }
