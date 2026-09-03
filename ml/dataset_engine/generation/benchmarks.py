from __future__ import annotations

import time
from dataclasses import dataclass

from .large_scale import generate_in_chunks


@dataclass(frozen=True)
class GenerationBenchmark:
    rows: int
    chunk_size: int
    elapsed_seconds: float

    @property
    def rows_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return float("inf")

        return self.rows / self.elapsed_seconds

    @property
    def rows_per_minute(self) -> float:
        return self.rows_per_second * 60


def benchmark_generation(
    rows: int,
    chunk_size: int = 100_000,
    seed: int = 42,
) -> GenerationBenchmark:
    if rows <= 0:
        raise ValueError("rows must be > 0")

    start = time.perf_counter()

    generated = 0

    for chunk in generate_in_chunks(
        rows=rows,
        chunk_size=chunk_size,
        seed=seed,
    ):
        generated += len(chunk)

    elapsed = time.perf_counter() - start

    if generated != rows:
        raise RuntimeError(
            f"Expected {rows} rows but generated {generated}."
        )

    return GenerationBenchmark(
        rows=rows,
        chunk_size=chunk_size,
        elapsed_seconds=elapsed,
    )
