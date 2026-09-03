from collections.abc import Iterable, Sequence

from .schemas import ClassificationRecord


class ClassificationDataset:
    """
    Dataset abstraction for transaction classification.

    Each record contains:
        text  -> transaction narration
        label -> transaction class
    """

    def __init__(
        self,
        records: Iterable[ClassificationRecord],
    ) -> None:
        self._records = tuple(records)

        if not self._records:
            raise ValueError(
                "Classification dataset cannot be empty."
            )

    @property
    def records(self) -> tuple[ClassificationRecord, ...]:
        return self._records

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(
            record.text
            for record in self._records
        )

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(
            record.label
            for record in self._records
        )

    @property
    def classes(self) -> tuple[str, ...]:
        return tuple(
            sorted(set(self.labels))
        )

    def __len__(self) -> int:
        return len(self._records)

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[str, str]],
    ) -> "ClassificationDataset":
        return cls(
            ClassificationRecord(
                text=text,
                label=label,
            )
            for text, label in pairs
        )

    def validate_classes(
        self,
        allowed_classes: Sequence[str],
    ) -> None:
        allowed = set(allowed_classes)

        unknown = sorted(
            set(self.labels) - allowed
        )

        if unknown:
            raise ValueError(
                "Dataset contains unknown transaction classes: "
                + ", ".join(unknown)
            )

    def class_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for label in self.labels:
            counts[label] = counts.get(label, 0) + 1

        return dict(sorted(counts.items()))
