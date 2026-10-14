# Closest Pair of Points

## Requirements
- Python 3.10+
- Matplotlib for plots: `python -m pip install matplotlib`

## Run
```bash
python closest_pair.py
```
Enter `N`. The program generates random 2D coordinates, prints the closest pair
and minimum distance from brute force and divide-and-conquer, reports timing,
checks that the distances agree, runs increasing-size benchmarks, and displays
a point plot plus a runtime comparison graph.

## Corner cases
- `N < 2`: no pair exists, so the result is N/A.
- Duplicate points: minimum distance is 0.
- Collinear points and points sharing x/y coordinates are supported.
- `N = 2`: the only pair is returned.
- Negative and floating-point coordinates are supported by the algorithms.

## Complexity
- Brute force: O(N²) time, O(1) auxiliary space (excluding input).
- Divide-and-conquer: O(N log N) expected textbook bound with sorted lists;
  this implementation uses sorting once and linear y-partitioning per level.
