from __future__ import annotations

import json
from pathlib import Path

from .schemas import DatasetManifest, DatasetVersion


def create_manifest(
    version: DatasetVersion,
) -> DatasetManifest:
    return DatasetManifest(
        version_id=version.version_id,
        dataset_name=version.dataset_name,
        version=version.version,
        seed=version.seed,
        source=version.source,
        description=version.description,
        created_at=version.created_at.isoformat(),
        total_rows=version.total_rows,
        train_rows=version.train_rows,
        validation_rows=version.validation_rows,
        test_rows=version.test_rows,
        checksum=version.checksum,
    )


def save_manifest(
    manifest: DatasetManifest,
    path: str | Path,
) -> Path:
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "version_id": manifest.version_id,
        "dataset_name": manifest.dataset_name,
        "version": manifest.version,
        "seed": manifest.seed,
        "source": manifest.source,
        "description": manifest.description,
        "created_at": manifest.created_at,
        "total_rows": manifest.total_rows,
        "train_rows": manifest.train_rows,
        "validation_rows": manifest.validation_rows,
        "test_rows": manifest.test_rows,
        "checksum": manifest.checksum,
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return path


def load_manifest(
    path: str | Path,
) -> DatasetManifest:
    path = Path(path)

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    return DatasetManifest(**payload)
