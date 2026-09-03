from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SplitConfig:
    train_ratio: float = 0.80
    validation_ratio: float = 0.10
    test_ratio: float = 0.10
    seed: int = 42
    stratify_by: str | None = "template_id"

    def validate(self) -> None:
        ratios = (
            self.train_ratio,
            self.validation_ratio,
            self.test_ratio,
        )

        if any(ratio <= 0 or ratio >= 1 for ratio in ratios):
            raise ValueError("All split ratios must be between 0 and 1.")

        if abs(sum(ratios) - 1.0) > 1e-9:
            raise ValueError(
                "train_ratio + validation_ratio + test_ratio must equal 1."
            )

        if not isinstance(self.seed, int):
            raise ValueError("seed must be an integer.")

        if self.stratify_by is not None and not isinstance(
            self.stratify_by, str
        ):
            raise ValueError("stratify_by must be a string or None.")


@dataclass(frozen=True)
class SplitStatistics:
    total_rows: int
    train_rows: int
    validation_rows: int
    test_rows: int

    @property
    def train_ratio(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.train_rows / self.total_rows

    @property
    def validation_ratio(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.validation_rows / self.total_rows

    @property
    def test_ratio(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.test_rows / self.total_rows


@dataclass(frozen=True)
class DatasetSplit:
    train: tuple
    validation: tuple
    test: tuple
    statistics: SplitStatistics
