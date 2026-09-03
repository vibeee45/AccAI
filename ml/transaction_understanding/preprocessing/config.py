from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessingConfig:
    lowercase: bool = True
    normalize_unicode: bool = True
    normalize_currency: bool = True
    normalize_punctuation: bool = True
    normalize_whitespace: bool = True
    normalize_accounting_terms: bool = True
