from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class EntityType(str, Enum):
    AMOUNT = "amount"
    CURRENCY = "currency"
    DATE = "date"
    PERSON = "person"
    ORGANIZATION = "organization"
    PAYMENT_REFERENCE = "payment_reference"
    ACCOUNT_REFERENCE = "account_reference"
    DESCRIPTION = "description"


@dataclass(frozen=True)
class ExtractedEntity:
    entity_type: EntityType
    text: str
    normalized_value: str
    start: int
    end: int
    confidence: float


@dataclass(frozen=True)
class EntityExtractionResult:
    original_text: str
    entities: tuple[ExtractedEntity, ...]

    @property
    def amounts(self) -> tuple[ExtractedEntity, ...]:
        return tuple(
            entity
            for entity in self.entities
            if entity.entity_type == EntityType.AMOUNT
        )

    @property
    def dates(self) -> tuple[ExtractedEntity, ...]:
        return tuple(
            entity
            for entity in self.entities
            if entity.entity_type == EntityType.DATE
        )

    @property
    def payment_references(self) -> tuple[ExtractedEntity, ...]:
        return tuple(
            entity
            for entity in self.entities
            if entity.entity_type == EntityType.PAYMENT_REFERENCE
        )

    @property
    def descriptions(self) -> tuple[ExtractedEntity, ...]:
        return tuple(
            entity
            for entity in self.entities
            if entity.entity_type == EntityType.DESCRIPTION
        )
