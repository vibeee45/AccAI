from dataclasses import dataclass


@dataclass(frozen=True)
class FailureHandlingConfig:
    capture_exception_details: bool = True
    preserve_metadata: bool = True
    max_error_message_length: int = 500

    def __post_init__(self) -> None:
        if not isinstance(
            self.capture_exception_details,
            bool,
        ):
            raise TypeError(
                "capture_exception_details must be bool."
            )

        if not isinstance(
            self.preserve_metadata,
            bool,
        ):
            raise TypeError(
                "preserve_metadata must be bool."
            )

        if (
            not isinstance(
                self.max_error_message_length,
                int,
            )
            or isinstance(
                self.max_error_message_length,
                bool,
            )
        ):
            raise TypeError(
                "max_error_message_length must be int."
            )

        if self.max_error_message_length <= 0:
            raise ValueError(
                "max_error_message_length must be greater than zero."
            )
