from collections.abc import Iterable, Iterator

from .schemas import FeedbackDataset, FeedbackExample


class FeedbackDatasetRepository:

    def __init__(self) -> None:
        self._examples: dict[str, FeedbackExample] = {}

    def add(
        self,
        example: FeedbackExample,
    ) -> FeedbackExample:
        if not isinstance(example, FeedbackExample):
            raise TypeError(
                "example must be a FeedbackExample"
            )

        if example.feedback_id in self._examples:
            raise ValueError(
                f"Feedback example already exists: "
                f"{example.feedback_id}"
            )

        self._examples[example.feedback_id] = example
        return example

    def add_many(
        self,
        examples: Iterable[FeedbackExample],
    ) -> int:
        added = 0

        for example in examples:
            self.add(example)
            added += 1

        return added

    def get(
        self,
        feedback_id: str,
    ) -> FeedbackExample | None:
        return self._examples.get(feedback_id)

    def get_by_transaction(
        self,
        transaction_id: str,
    ) -> list[FeedbackExample]:
        return [
            example
            for example in self._examples.values()
            if example.transaction_id == transaction_id
        ]

    def list_all(self) -> list[FeedbackExample]:
        return list(self._examples.values())

    def list_approved(self) -> list[FeedbackExample]:
        return [
            example
            for example in self._examples.values()
            if example.is_approved
        ]

    def list_rejected(self) -> list[FeedbackExample]:
        return [
            example
            for example in self._examples.values()
            if example.is_rejected
        ]

    def remove(
        self,
        feedback_id: str,
    ) -> FeedbackExample | None:
        return self._examples.pop(feedback_id, None)

    def contains(
        self,
        feedback_id: str,
    ) -> bool:
        return feedback_id in self._examples

    def clear(self) -> None:
        self._examples.clear()

    def __len__(self) -> int:
        return len(self._examples)

    def __iter__(self) -> Iterator[FeedbackExample]:
        return iter(self._examples.values())

    def build_dataset(
        self,
        metadata: dict | None = None,
    ) -> FeedbackDataset:
        return FeedbackDataset(
            examples=tuple(self._examples.values()),
            metadata=metadata or {},
        )
