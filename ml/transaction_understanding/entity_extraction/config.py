from dataclasses import dataclass


@dataclass(frozen=True)
class EntityExtractionConfig:
    extract_amounts: bool = True
    extract_currencies: bool = True
    extract_dates: bool = True
    extract_payment_references: bool = True
    extract_people: bool = True
    extract_organizations: bool = True
    extract_descriptions: bool = True
