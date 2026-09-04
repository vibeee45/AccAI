from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredOutputConfig:
    include_entities: bool = True
    include_semantic_matches: bool = True
    include_metadata: bool = True
    include_reasons: bool = True

    def __post_init__(self) -> None:
        if not isinstance(
            self.include_entities,
            bool,
        ):
            raise TypeError(
                "include_entities must be bool."
            )

        if not isinstance(
            self.include_semantic_matches,
            bool,
        ):
            raise TypeError(
                "include_semantic_matches must be bool."
            )

        if not isinstance(
            self.include_metadata,
            bool,
        ):
            raise TypeError(
                "include_metadata must be bool."
            )

        if not isinstance(
            self.include_reasons,
            bool,
        ):
            raise TypeError(
                "include_reasons must be bool."
            )
