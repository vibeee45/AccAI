from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticMatch:
    index: int
    text: str
    similarity: float

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("index cannot be negative.")

        if not self.text.strip():
            raise ValueError("text cannot be empty.")

        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError(
                "similarity must be between 0 and 1."
            )


@dataclass(frozen=True)
class SemanticMatchResult:
    query: str
    matches: list[SemanticMatch]

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query cannot be empty.")

        if not isinstance(self.matches, list):
            raise TypeError("matches must be a list.")
