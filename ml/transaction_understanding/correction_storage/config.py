from dataclasses import dataclass


@dataclass(frozen=True)
class CorrectionStorageConfig:
    """
    Configuration for human-review correction storage.
    """

    max_reason_length: int = 500
    max_metadata_entries: int = 100
    max_records: int = 100000

    def __post_init__(self) -> None:
        if self.max_reason_length <= 0:
            raise ValueError(
                "max_reason_length must be greater than 0."
            )

        if self.max_metadata_entries <= 0:
            raise ValueError(
                "max_metadata_entries must be greater than 0."
            )

        if self.max_records <= 0:
            raise ValueError(
                "max_records must be greater than 0."
            )
