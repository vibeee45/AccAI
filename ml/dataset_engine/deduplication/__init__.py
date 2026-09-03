from .deduplicator import deduplicate_records
from .fingerprints import (
    record_fingerprint,
    semantic_fingerprint,
)
from .schemas import (
    DeduplicationConfig,
    DeduplicationResult,
    DeduplicationStats,
    DuplicateRecord,
)

__all__ = [
    "DeduplicationConfig",
    "DeduplicationResult",
    "DeduplicationStats",
    "DuplicateRecord",
    "deduplicate_records",
    "record_fingerprint",
    "semantic_fingerprint",
]
