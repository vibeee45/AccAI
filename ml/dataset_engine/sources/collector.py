from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from .manifest import DatasetSource


@dataclass(frozen=True)
class CollectedDataset:
    """Metadata describing a collected dataset file."""

    source_id: str
    source_url: str
    local_path: Path
    sha256: str
    size_bytes: int


class DatasetCollectionError(RuntimeError):
    """Raised when public dataset collection fails."""


def calculate_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Calculate SHA-256 checksum for a local file.

    Files are read in chunks so large datasets do not need to
    be loaded completely into memory.
    """

    if not path.is_file():
        raise DatasetCollectionError(
            f"Cannot calculate checksum. File does not exist: {path}"
        )

    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def download_file(
    url: str,
    destination: Path,
    *,
    timeout: int = 60,
    overwrite: bool = False,
) -> Path:
    """
    Download a file from a direct HTTP(S) URL.

    This function is intentionally generic. Authentication-dependent
    sources such as Kaggle are handled separately rather than
    embedding credentials into ACCAI.
    """

    if destination.exists() and not overwrite:
        raise DatasetCollectionError(
            f"Destination already exists: {destination}"
        )

    if not url.startswith(("http://", "https://")):
        raise DatasetCollectionError(
            f"Unsupported URL: {url}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    request = Request(
        url,
        headers={
            "User-Agent": "ACCAI-Dataset-Engine/1.0",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            with destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)

    except Exception as exc:
        if destination.exists():
            destination.unlink()

        raise DatasetCollectionError(
            f"Failed to download dataset from {url}: {exc}"
        ) from exc

    return destination


def collect_local_file(
    source: DatasetSource,
    file_path: Path,
) -> CollectedDataset:
    """
    Register an already downloaded local dataset file.

    No contents are modified.
    """

    if not file_path.is_file():
        raise DatasetCollectionError(
            f"Dataset file does not exist: {file_path}"
        )

    return CollectedDataset(
        source_id=source.source_id,
        source_url=source.url,
        local_path=file_path,
        sha256=calculate_sha256(file_path),
        size_bytes=file_path.stat().st_size,
    )


def validate_collected_dataset(
    dataset: CollectedDataset,
) -> None:
    """Validate collection metadata against the local file."""

    if not dataset.source_id.strip():
        raise DatasetCollectionError(
            "Collected dataset source ID cannot be empty."
        )

    if not dataset.source_url.startswith(
        ("http://", "https://")
    ):
        raise DatasetCollectionError(
            f"Invalid source URL: {dataset.source_url}"
        )

    if not dataset.local_path.is_file():
        raise DatasetCollectionError(
            f"Collected dataset file does not exist: "
            f"{dataset.local_path}"
        )

    if dataset.size_bytes < 0:
        raise DatasetCollectionError(
            "Dataset size cannot be negative."
        )

    if len(dataset.sha256) != 64:
        raise DatasetCollectionError(
            "Invalid SHA-256 checksum."
        )