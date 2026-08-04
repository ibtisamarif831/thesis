"""Label-independent agreement measurements."""

from __future__ import annotations

import math
from collections import Counter


def _comb2(value: int) -> int:
    return value * (value - 1) // 2


def cross_table(left: list[int], right: list[int]) -> dict[str, object]:
    left_values = sorted(set(left))
    right_values = sorted(set(right))
    counts = Counter(zip(left, right, strict=True))
    return {
        "feature_labels": left_values,
        "ai_labels": right_values,
        "counts": [[counts[(a, b)] for b in right_values] for a in left_values],
    }


def adjusted_rand_index(left: list[int], right: list[int]) -> float:
    n = len(left)
    if n != len(right) or n < 2:
        return 1.0 if left == right else 0.0
    cells = Counter(zip(left, right, strict=True))
    rows, columns = Counter(left), Counter(right)
    sum_cells = sum(_comb2(value) for value in cells.values())
    sum_rows = sum(_comb2(value) for value in rows.values())
    sum_columns = sum(_comb2(value) for value in columns.values())
    pairs = _comb2(n)
    expected = sum_rows * sum_columns / pairs
    maximum = (sum_rows + sum_columns) / 2
    denominator = maximum - expected
    return 1.0 if denominator == 0 and sum_cells == maximum else (sum_cells - expected) / denominator if denominator else 0.0


def normalized_mutual_information(left: list[int], right: list[int]) -> float:
    n = len(left)
    if n != len(right) or not n:
        return 0.0
    cells = Counter(zip(left, right, strict=True))
    rows, columns = Counter(left), Counter(right)
    mutual_information = 0.0
    for (a, b), count in cells.items():
        mutual_information += count / n * math.log((count * n) / (rows[a] * columns[b]))
    left_entropy = -sum(count / n * math.log(count / n) for count in rows.values())
    right_entropy = -sum(count / n * math.log(count / n) for count in columns.values())
    denominator = math.sqrt(left_entropy * right_entropy)
    return 1.0 if denominator == 0 and left == right else mutual_information / denominator if denominator else 0.0


def pairwise_same_cluster_agreement(left: list[int], right: list[int]) -> float:
    if len(left) != len(right):
        raise ValueError("Label sequences must have the same length")
    agreements = total = 0
    for first in range(len(left)):
        for second in range(first + 1, len(left)):
            total += 1
            agreements += (left[first] == left[second]) == (right[first] == right[second])
    return agreements / total if total else 1.0


def agreement_metrics(left: list[int], right: list[int]) -> dict[str, object]:
    return {
        "adjusted_rand_index": adjusted_rand_index(left, right),
        "normalized_mutual_information": normalized_mutual_information(left, right),
        "pairwise_same_cluster_agreement": pairwise_same_cluster_agreement(left, right),
        "cross_table": cross_table(left, right),
    }
