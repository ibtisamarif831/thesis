"""Select strong, complementary representatives from visual feature families."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence


def select_strong_family_features(
    features: Iterable[dict],
    pairs: Iterable[dict],
    family_order: Sequence[str],
    strength_priority: Mapping[str, Sequence[str]],
    per_family: int = 2,
    max_abs_spearman: float = 0.70,
) -> list[dict]:
    """Select strength-ranked features while rejecting directly redundant pairs.

    ``strength_priority`` carries the substantive ranking: literature support,
    interpretability, measurement directness, and observed data quality. Spearman
    correlation is deliberately used only after that ranking, as a pairwise
    redundancy screen between representatives that would actually be selected.
    """

    if per_family < 1:
        raise ValueError("per_family must be at least 1")
    if not 0.0 < max_abs_spearman <= 1.0:
        raise ValueError("max_abs_spearman must be in the interval (0, 1]")

    grouped: dict[str, dict[str, dict]] = defaultdict(dict)
    for feature in features:
        family_id = str(feature.get("group", ""))
        feature_id = str(feature.get("feature_id", ""))
        if feature_id:
            grouped[family_id][feature_id] = feature

    pair_lookup: dict[frozenset[str], tuple[float, float]] = {}
    for pair in pairs:
        feature_a = str(pair.get("feature_a", ""))
        feature_b = str(pair.get("feature_b", ""))
        if not feature_a or not feature_b or feature_a == feature_b:
            continue
        correlation = float(pair.get("correlation", 0.0))
        abs_correlation = float(pair.get("abs_correlation", abs(correlation)))
        pair_lookup[frozenset((feature_a, feature_b))] = (correlation, abs_correlation)

    selected: list[dict] = []
    for family_id in family_order:
        family_features = grouped.get(family_id, {})
        ranked_candidates = []
        for priority_rank, feature_id in enumerate(strength_priority.get(family_id, ()), start=1):
            feature = family_features.get(feature_id)
            if feature is None or float(feature.get("std", 0.0)) <= 1e-12:
                continue
            ranked_candidates.append((priority_rank, feature))

        family_selected: list[tuple[int, dict]] = []
        for priority_rank, candidate in ranked_candidates:
            if len(family_selected) >= per_family:
                break
            candidate_id = str(candidate["feature_id"])
            if family_selected:
                correlations = [
                    pair_lookup.get(frozenset((candidate_id, str(existing["feature_id"]))))
                    for _, existing in family_selected
                ]
                if any(
                    correlation is None or correlation[1] >= max_abs_spearman
                    for correlation in correlations
                ):
                    continue
            family_selected.append((priority_rank, candidate))

        for selection_rank, (priority_rank, feature) in enumerate(family_selected, start=1):
            companion = next(
                (other for _, other in family_selected if other["feature_id"] != feature["feature_id"]),
                None,
            )
            pair_correlation = (
                pair_lookup.get(frozenset((str(feature["feature_id"]), str(companion["feature_id"]))))
                if companion is not None
                else None
            )
            selected.append(
                feature
                | {
                    "selection_rank_in_family": selection_rank,
                    "strength_priority_rank": priority_rank,
                    "selection_metric": "strength priority with direct pairwise Spearman screening",
                    "companion_feature_id": str(companion["feature_id"]) if companion else "",
                    "companion_feature_label": str(companion.get("label", "")) if companion else "",
                    "pair_correlation": pair_correlation[0] if pair_correlation else None,
                    "pair_abs_correlation": pair_correlation[1] if pair_correlation else None,
                }
            )
    return selected
