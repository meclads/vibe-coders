"""Closest-pair algorithms and timing helpers."""

from __future__ import annotations

import math
import time
from typing import Optional

Point = tuple[float, float]
Pair = tuple[Point, Point]


def canonical_pair(first: Point, second: Point) -> Pair:
    """Return a pair in stable coordinate order."""
    return (first, second) if first <= second else (second, first)


def squared_distance(first: Point, second: Point) -> float:
    dx = first[0] - second[0]
    dy = first[1] - second[1]
    return dx * dx + dy * dy


def brute_force(points: list[Point]) -> tuple[float, Optional[Pair]]:
    """Return the closest distance and pair in O(N^2) time."""
    if len(points) < 2:
        return math.inf, None

    best_squared = math.inf
    best_pair = None
    for first_index in range(len(points) - 1):
        for second_index in range(first_index + 1, len(points)):
            pair = canonical_pair(points[first_index], points[second_index])
            candidate = squared_distance(*pair)
            if candidate < best_squared or (
                candidate == best_squared and (best_pair is None or pair < best_pair)
            ):
                best_squared, best_pair = candidate, pair
    return math.sqrt(best_squared), best_pair


def divide_and_conquer(
    points: list[Point],
) -> tuple[float, Optional[Pair], Optional[dict]]:
    """Return the closest pair and top-level split/strip data in O(N log N)."""
    if len(points) < 2:
        return math.inf, None, None

    tagged = [(point[0], point[1], index) for index, point in enumerate(points)]
    by_x = sorted(tagged, key=lambda item: (item[0], item[1], item[2]))
    by_y = sorted(tagged, key=lambda item: (item[1], item[0], item[2]))

    duplicates: dict[Point, int] = {}
    for x, y, _ in by_x:
        duplicates[(x, y)] = duplicates.get((x, y), 0) + 1
    repeated_points = [point for point, count in duplicates.items() if count > 1]
    if repeated_points:
        repeated = min(repeated_points)
        pair = (repeated, repeated)
        split_index = len(by_x) // 2
        split_x = (by_x[split_index - 1][0] + by_x[split_index][0]) / 2
        return 0.0, pair, {
            "split_x": split_x,
            "distance": 0.0,
            "final_distance": 0.0,
            "strip_left": split_x,
            "strip_right": split_x,
            "strip_points": [point for point in points if point[0] == split_x],
        }

    top_trace = None

    def coordinate_pair(first, second) -> Pair:
        return canonical_pair((first[0], first[1]), (second[0], second[1]))

    def recurse(xs, ys, top_level=False):
        nonlocal top_trace
        count = len(xs)
        if count <= 3:
            best_squared = math.inf
            best_pair = None
            for first_index in range(count - 1):
                for second_index in range(first_index + 1, count):
                    pair = coordinate_pair(xs[first_index], xs[second_index])
                    candidate = squared_distance(*pair)
                    if candidate < best_squared or (
                        candidate == best_squared and (best_pair is None or pair < best_pair)
                    ):
                        best_squared, best_pair = candidate, pair
            return best_squared, best_pair

        middle = count // 2
        left_x = xs[:middle]
        right_x = xs[middle:]
        left_ids = {item[2] for item in left_x}
        left_y, right_y = [], []
        for item in ys:
            (left_y if item[2] in left_ids else right_y).append(item)

        left_squared, left_pair = recurse(left_x, left_y)
        right_squared, right_pair = recurse(right_x, right_y)
        if left_squared < right_squared:
            best_squared, best_pair = left_squared, left_pair
        elif right_squared < left_squared:
            best_squared, best_pair = right_squared, right_pair
        else:
            best_squared = left_squared
            pairs = [pair for pair in (left_pair, right_pair) if pair is not None]
            best_pair = min(pairs) if pairs else None

        split_x = (left_x[-1][0] + right_x[0][0]) / 2
        delta = math.sqrt(best_squared)
        strip = [item for item in ys if abs(item[0] - split_x) <= delta]
        if top_level:
            top_trace = {
                "split_x": split_x,
                "distance": delta,
                "final_distance": delta,
                "strip_left": split_x - delta,
                "strip_right": split_x + delta,
                "strip_points": [(item[0], item[1]) for item in strip],
            }

        for first_index, first in enumerate(strip):
            second_index = first_index + 1
            while (
                second_index < len(strip)
                and (strip[second_index][1] - first[1]) ** 2 <= best_squared
            ):
                second = strip[second_index]
                pair = coordinate_pair(first, second)
                candidate = squared_distance(*pair)
                if candidate < best_squared or (
                    candidate == best_squared and (best_pair is None or pair < best_pair)
                ):
                    best_squared, best_pair = candidate, pair
                second_index += 1

        if top_level and top_trace is not None:
            top_trace["final_distance"] = math.sqrt(best_squared)
        return best_squared, best_pair

    best_squared, best_pair = recurse(by_x, by_y, top_level=True)
    return math.sqrt(best_squared), best_pair, top_trace


def timed_brute(points: list[Point]):
    start = time.perf_counter()
    result = brute_force(points)
    return result, (time.perf_counter() - start) * 1000


def timed_divide(points: list[Point]):
    start = time.perf_counter()
    result = divide_and_conquer(points)
    return result, (time.perf_counter() - start) * 1000


def format_pair(pair: Optional[Pair]) -> str:
    if pair is None:
        return "N/A"
    first, second = pair
    return (
        f"({first[0]:.6f}, {first[1]:.6f}) and "
        f"({second[0]:.6f}, {second[1]:.6f})"
    )