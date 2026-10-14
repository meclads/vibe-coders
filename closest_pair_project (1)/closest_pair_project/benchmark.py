"""Reproducible, same-dataset benchmarking for closest-pair algorithms."""

from __future__ import annotations

import math
import random
from typing import Callable, Optional

from closest_pair import Point, timed_brute, timed_divide


DEFAULT_SIZES = (100, 200, 400, 800, 1200, 1600)


def benchmark(
    sizes: list[int],
    seed: int = 2026,
    progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict[str, float | int]]:
    """Benchmark both algorithms on the same reproducible points per size."""
    rows: list[dict[str, float | int]] = []
    for index, size in enumerate(sizes, start=1):
        if size < 2:
            raise ValueError("Benchmark sizes must be at least 2.")
        rng = random.Random(seed + size)
        points = [
            (rng.uniform(-1000.0, 1000.0), rng.uniform(-1000.0, 1000.0))
            for _ in range(size)
        ]
        (brute_distance, _), brute_ms = timed_brute(points)
        (divide_distance, _, _), divide_ms = timed_divide(points)
        if not math.isclose(brute_distance, divide_distance, rel_tol=1e-10, abs_tol=1e-10):
            raise AssertionError(
                f"Algorithms disagree for N={size}: {brute_distance} vs {divide_distance}"
            )
        rows.append({
            "n": size,
            "brute_ms": brute_ms,
            "divide_ms": divide_ms,
            "distance": brute_distance,
        })
        if progress:
            progress(index, len(sizes))
    return rows


def benchmark_sizes(maximum: int) -> list[int]:
    """Return standard benchmark sizes up to the configured maximum."""
    if maximum < 2:
        raise ValueError("Maximum benchmark N must be at least 2.")
    sizes = [size for size in DEFAULT_SIZES if size <= maximum]
    if maximum not in sizes:
        sizes.append(maximum)
    return sorted(set(sizes))