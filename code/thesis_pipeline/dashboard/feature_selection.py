"""Select low-redundancy features from Spearman review results."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence


def select_unique_family_features(
    features: Iterable[dict],
    family_order: Sequence[str],
    per_family: int = 2,
) -> list[dict]:
    """Pick informative features with the lowest strongest Spearman redundancy."""

    if per_family < 1:
        raise ValueError("per_family must be at least 1")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for feature in features:
        grouped[str(feature.get("group", ""))].append(feature)

    selected: list[dict] = []
    for family_id in family_order:
        candidates = sorted(
            grouped.get(family_id, []),
            key=lambda feature: (
                float(feature.get("std", 0.0)) <= 1e-12,
                float(feature.get("strongest_abs_correlation", 0.0)),
                -float(feature.get("std", 0.0)),
                str(feature.get("label", "")),
            ),
        )
        for rank, feature in enumerate(candidates[:per_family], start=1):
            selected.append(
                feature
                | {
                    "uniqueness_rank_in_family": rank,
                    "selection_metric": "lowest strongest absolute Spearman correlation",
                }
            )
    return selected
