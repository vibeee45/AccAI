from collections.abc import Iterable

from ..correction_storage.schemas import CorrectionRecord
from .builder import FeedbackDatasetBuilder
from .config import FeedbackDatasetConfig
from .dataset import FeedbackDatasetRepository
from .schemas import FeedbackDataset, FeedbackExample


class FeedbackDatasetService:

    def __init__(
        self,
        config: FeedbackDatasetConfig | None = None,
        repository: FeedbackDatasetRepository | None = None,
    ) -> None:
        self.config = config or FeedbackDatasetConfig()

        self.repository = (
            repository
            or FeedbackDatasetRepository()
        )

        self.builder = FeedbackDatasetBuilder(
            self.config
        )

    def create_example(
        self,
        correction: CorrectionRecord,
    ) -> FeedbackExample:
        return self.builder.build_example(
            correction
        )

    def build(
        self,
        corrections: Iterable[CorrectionRecord],
    ) -> FeedbackDataset:
        dataset = self.builder.build(
            corrections
        )

        self.repository.clear()
        self.repository.add_many(
            dataset.examples
        )

        return dataset

    def add_correction(
        self,
        correction: CorrectionRecord,
    ) -> FeedbackExample | None:
        if not self.builder.should_include(
            correction
        ):
            return None

        example = self.builder.build_example(
            correction
        )

        if self.config.deduplicate:
            existing = self.repository.get_by_transaction(
                correction.transaction_id
            )

            for item in existing:
                if item.review_id == correction.review_id:
                    return item

        self.repository.add(example)

        return example

    def get(
        self,
        feedback_id: str,
    ) -> FeedbackExample | None:
        return self.repository.get(
            feedback_id
        )

    def get_by_transaction(
        self,
        transaction_id: str,
    ) -> list[FeedbackExample]:
        return self.repository.get_by_transaction(
            transaction_id
        )

    def list_all(self) -> list[FeedbackExample]:
        return self.repository.list_all()

    def list_approved(self) -> list[FeedbackExample]:
        return self.repository.list_approved()

    def list_rejected(self) -> list[FeedbackExample]:
        return self.repository.list_rejected()

    def dataset(self) -> FeedbackDataset:
        return self.repository.build_dataset(
            metadata={
                "source": "feedback_dataset_repository",
            }
        )

    def clear(self) -> None:
        self.repository.clear()

    def __len__(self) -> int:
        return len(self.repository)
