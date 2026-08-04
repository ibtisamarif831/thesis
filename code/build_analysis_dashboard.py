#!/usr/bin/env python3
"""Build Analysis clustering data and a static Plotly dashboard."""

from __future__ import annotations

import csv
import html
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import build_clustering_metadata_sample as metadata_helpers
import extract_icon_features
from thesis_pipeline.features import registry as feature_registry
from thesis_pipeline.clustering import (
    hierarchical_single_linkage_labels,
    kmeans,
    pairwise_distances,
    pca_2d,
    silhouette_proxy,
    standardize,
)


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "icon_data" / "analysis"
DATASET_PATH = ANALYSIS_DIR / "dataset.csv"
FEATURES_PATH = ANALYSIS_DIR / "features.csv"
OUTPUT_DIR = ANALYSIS_DIR / "analysis_dashboard"
ASSETS_DIR = OUTPUT_DIR / "assets"
PLOTLY_ASSET = ASSETS_DIR / "plotly.min.js"

PER_SET_SAMPLE_SIZE = 10
FEATURE_GROUP_BIN_COUNT = 10
FEATURE_GROUP_SAMPLES_PER_BIN = 2
FEATURE_GROUP_SAMPLE_SIZE = FEATURE_GROUP_BIN_COUNT * FEATURE_GROUP_SAMPLES_PER_BIN
FEATURE_GROUP_COMPARISON_SIZE = 3
K_VALUES = (3, 5, 7, 10)
PRIMARY_K = 7
RANDOM_SEED = 42

METADATA_COLUMNS = [
    "icon_id",
    "set_id",
    "set_name",
    "icon_name",
    "label",
    "source",
    "source_url",
    "format",
    "filename",
    "relative_path",
    "normalized_path",
    "notes",
    "metadata_text",
    "metadata_tokens",
    "has_notes",
    "source_path_exists",
    "normalized_path_exists",
]

IMAGE_FEATURE_COLUMNS = list(feature_registry.raw_feature_ids())
GRID_FEATURE_COLUMNS = [f"grid_foreground_{row}_{col}" for row in range(4) for col in range(4)]
EXCLUDED_IMAGE_FEATURES = set(feature_registry.excluded_feature_ids())
EXCLUDED_IMAGE_FEATURE_REASONS = dict(feature_registry.excluded_feature_reasons())
DASHBOARD_FEATURE_SECTIONS = [
    {
        "id": family.id,
        "title": family.title,
        "description": family.description,
        "human_category": family.human_category,
        "family_summary": family.family_summary,
        "perception": family.perception,
        "low_value": family.low_value,
        "high_value": family.high_value,
        "representative_feature_id": family.representative_feature_id,
        "representative_interpretation": family.representative_interpretation,
        "representative_rationale": family.representative_rationale,
        "representative_evidence": family.representative_evidence,
        "representative_citation": family.representative_citation,
        "feature_ids": list(family.feature_ids),
        "visible": family.visible,
    }
    for family in feature_registry.family_specs()
]
FEATURE_LABELS = dict(feature_registry.feature_labels())
FEATURE_MEANINGS = dict(feature_registry.feature_meanings())
FEATURE_CATEGORY_REASONS = dict(feature_registry.feature_category_reasons())
FEATURE_VISUAL_CATEGORIZATIONS = {
    key: list(value) for key, value in feature_registry.feature_visual_categorizations().items()
}
FEATURE_VISUAL_CATEGORY_LABELS = dict(feature_registry.feature_visual_category_labels())

MCDOUGALL_NUMERIC_COLUMNS = [
    "mcdougall_concreteness",
    "mcdougall_complexity",
    "mcdougall_familiarity",
    "mcdougall_meaningfulness",
    "mcdougall_semantic_distance",
    "mcdougall_concept_agreement",
    "mcdougall_name_agreement",
]

FEATURE_VARIANTS = ("image", "metadata", "combined")
REDUNDANCY_HIGH_THRESHOLD = 0.85
REDUNDANCY_MODERATE_THRESHOLD = 0.70


def image_feature_sections() -> list[dict[str, object]]:
    """Return the legacy dashboard serialization of the shared feature registry."""

    return feature_registry.dashboard_sections()


def active_image_feature_columns() -> list[str]:
    return list(feature_registry.analysis_feature_ids())


def active_image_feature_groups() -> list[list[str]]:
    return [list(group) for group in feature_registry.analysis_feature_groups()]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sample_random_rows_per_set(rows: list[dict[str, str]], per_set_sample_size: int, seed: int) -> list[dict[str, str]]:
    rows_by_set: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for index, row in enumerate(rows):
        rows_by_set[row["set_id"]].append((index, row))

    rng = np.random.default_rng(seed)
    indices = []
    for set_id in sorted(rows_by_set):
        set_rows = rows_by_set[set_id]
        if len(set_rows) <= per_set_sample_size:
            indices.extend(index for index, _ in set_rows)
            continue
        local_indices = rng.choice(len(set_rows), size=per_set_sample_size, replace=False).tolist()
        indices.extend(set_rows[local_index][0] for local_index in local_indices)

    indices = sorted(indices)
    return [rows[index] for index in indices]


def enrich_metadata_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ratings = metadata_helpers.load_mcdougall_ratings()
    enriched = []
    for source in rows:
        row = source.copy()
        set_id = row["set_id"]
        label = row.get("label", "")
        notes = row.get("notes", "")
        rating = None

        if set_id == "01_mcdougall_symbol_icon_set":
            appendix_item = metadata_helpers.notes_value(notes, "appendix_item")
            rating = ratings.get(appendix_item)
            if rating:
                rating_note = (
                    "mcdougall_ratings="
                    f"concreteness:{rating.get('concreteness', '')},"
                    f"complexity:{rating.get('complexity', '')},"
                    f"familiarity:{rating.get('familiarity', '')},"
                    f"meaningfulness:{rating.get('meaningfulness', '')},"
                    f"semantic_distance:{rating.get('semantic_distance', '')},"
                    f"concept_agreement:{rating.get('concept_agreement', '')},"
                    f"name_agreement:{rating.get('name_agreement', '')},"
                    f"common_response:{rating.get('common_response', '')}"
                )
                notes = "; ".join(part for part in [notes, rating_note] if part)

        metadata_text = " | ".join(value for value in [label, row.get("set_name", ""), notes] if value)
        enriched.append(
            {
                "icon_id": row["icon_id"],
                "set_id": set_id,
                "set_name": row["set_name"],
                "icon_name": label,
                "label": label,
                "source": row.get("source", ""),
                "source_url": row.get("source_url", ""),
                "format": row.get("format", ""),
                "filename": row.get("filename", ""),
                "relative_path": row.get("relative_path", ""),
                "normalized_path": row.get("normalized_path", ""),
                "notes": notes,
                "metadata_text": metadata_text,
                "metadata_tokens": metadata_helpers.text_tokens(label, row.get("set_name", ""), notes),
                "mcdougall_concreteness": (rating or {}).get("concreteness", ""),
                "mcdougall_complexity": (rating or {}).get("complexity", ""),
                "mcdougall_familiarity": (rating or {}).get("familiarity", ""),
                "mcdougall_meaningfulness": (rating or {}).get("meaningfulness", ""),
                "mcdougall_semantic_distance": (rating or {}).get("semantic_distance", ""),
                "mcdougall_concept_agreement": (rating or {}).get("concept_agreement", ""),
                "mcdougall_name_agreement": (rating or {}).get("name_agreement", ""),
                "mcdougall_common_response": (rating or {}).get("common_response", ""),
                "has_notes": str(bool(notes)).lower(),
                "source_path_exists": str((ROOT / row.get("relative_path", "")).exists()).lower(),
                "normalized_path_exists": str((ROOT / row.get("normalized_path", "")).exists()).lower(),
            }
        )
    return enriched


def extract_features(rows: list[dict[str, str]]) -> list[dict]:
    feature_rows = []
    failures = []
    for index, row in enumerate(rows, start=1):
        values, failure = extract_icon_features.extract_row(
            row,
            extract_icon_features.FEATURE_EXTRACTORS,
            foreground_threshold=245,
        )
        if failure:
            failures.append(failure)
            continue
        feature_rows.append(values)
        if index % 250 == 0:
            print(f"Extracted features for {index}/{len(rows)} rows")

    (OUTPUT_DIR / "feature_failures.json").write_text(
        json.dumps(failures, indent=2) + "\n", encoding="utf-8"
    )
    if failures:
        print(f"Feature extraction failures: {len(failures)}")
    return feature_rows


def to_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def to_optional_float(value: object) -> float | None:
    """Return a finite numeric value without turning missing data into a meaningful zero."""
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def finite_float(value: object) -> float:
    if value is None or value == "":
        return float("nan")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    if math.isnan(number) or math.isinf(number):
        return float("nan")
    return number


def average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.zeros(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = (start + end - 1) / 2.0 + 1.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def spearman_correlation(left: np.ndarray, right: np.ndarray) -> tuple[float, int]:
    mask = np.isfinite(left) & np.isfinite(right)
    pair_count = int(mask.sum())
    if pair_count < 2:
        return 0.0, pair_count
    left_ranks = average_ranks(left[mask])
    right_ranks = average_ranks(right[mask])
    left_std = left_ranks.std()
    right_std = right_ranks.std()
    if left_std == 0 or right_std == 0:
        return 0.0, pair_count
    correlation = float(np.corrcoef(left_ranks, right_ranks)[0, 1])
    if math.isnan(correlation) or math.isinf(correlation):
        return 0.0, pair_count
    return correlation, pair_count


def redundancy_band(abs_correlation: float) -> str:
    if abs_correlation >= REDUNDANCY_HIGH_THRESHOLD:
        return "high"
    if abs_correlation >= REDUNDANCY_MODERATE_THRESHOLD:
        return "moderate"
    return "low"


def title_case(value: str) -> str:
    return value.replace("_", " ").title()


def feature_metadata_by_id() -> dict[str, dict[str, str]]:
    metadata = {}
    for section in image_feature_sections():
        for feature in section["features"]:
            metadata[feature["id"]] = {
                "label": feature["label"],
                "group": feature["group"],
                "group_title": feature["group_title"],
                "meaning": feature["meaning"],
            }
    return metadata


def feature_review_source_rows(feature_by_id: dict[str, dict]) -> tuple[list[dict], str]:
    if FEATURES_PATH.exists():
        rows = read_csv(FEATURES_PATH)
        if rows and all(column in rows[0] for column in IMAGE_FEATURE_COLUMNS):
            return rows, FEATURES_PATH.relative_to(ROOT).as_posix()
    return list(feature_by_id.values()), "analysis_dashboard_sample"


def build_feature_review(feature_by_id: dict[str, dict]) -> dict:
    rows, source = feature_review_source_rows(feature_by_id)
    metadata = feature_metadata_by_id()
    active_columns = active_image_feature_columns()
    matrix = np.array(
        [[finite_float(row.get(column)) for column in active_columns] for row in rows],
        dtype=float,
    )

    feature_rows = []
    for column_index, feature_id in enumerate(active_columns):
        values = matrix[:, column_index]
        valid_values = values[np.isfinite(values)]
        feature_rows.append(
            {
                "feature_id": feature_id,
                "label": metadata.get(feature_id, {}).get("label", FEATURE_LABELS.get(feature_id, title_case(feature_id))),
                "group": metadata.get(feature_id, {}).get("group", ""),
                "group_title": metadata.get(feature_id, {}).get("group_title", ""),
                "meaning": metadata.get(feature_id, {}).get("meaning", ""),
                "std": round(float(valid_values.std()) if len(valid_values) else 0.0, 6),
                "variance": round(float(valid_values.var()) if len(valid_values) else 0.0, 6),
                "missing_count": int(len(values) - len(valid_values)),
                "strongest_abs_correlation": 0.0,
                "strongest_correlation": 0.0,
                "strongest_partner": "",
                "strongest_partner_label": "",
                "strongest_partner_group": "",
                "redundancy_band": "low",
            }
        )

    pair_rows = []
    feature_index = {row["feature_id"]: index for index, row in enumerate(feature_rows)}
    for left_index, left_feature in enumerate(active_columns):
        for right_index in range(left_index + 1, len(active_columns)):
            right_feature = active_columns[right_index]
            correlation, pair_count = spearman_correlation(matrix[:, left_index], matrix[:, right_index])
            abs_correlation = abs(correlation)
            left_meta = feature_rows[left_index]
            right_meta = feature_rows[right_index]
            pair_rows.append(
                {
                    "feature_a": left_feature,
                    "feature_a_label": left_meta["label"],
                    "feature_a_group": left_meta["group"],
                    "feature_a_group_title": left_meta["group_title"],
                    "feature_b": right_feature,
                    "feature_b_label": right_meta["label"],
                    "feature_b_group": right_meta["group"],
                    "feature_b_group_title": right_meta["group_title"],
                    "correlation": round(correlation, 6),
                    "abs_correlation": round(abs_correlation, 6),
                    "band": redundancy_band(abs_correlation),
                    "shared_group": left_meta["group"] == right_meta["group"],
                    "pair_count": pair_count,
                }
            )

            for feature_id, partner_id, partner_meta in (
                (left_feature, right_feature, right_meta),
                (right_feature, left_feature, left_meta),
            ):
                row = feature_rows[feature_index[feature_id]]
                if abs_correlation > row["strongest_abs_correlation"]:
                    row["strongest_abs_correlation"] = round(abs_correlation, 6)
                    row["strongest_correlation"] = round(correlation, 6)
                    row["strongest_partner"] = partner_id
                    row["strongest_partner_label"] = partner_meta["label"]
                    row["strongest_partner_group"] = partner_meta["group_title"]
                    row["redundancy_band"] = redundancy_band(abs_correlation)

    pair_rows.sort(key=lambda row: (-row["abs_correlation"], row["feature_a_label"], row["feature_b_label"]))
    feature_rows.sort(key=lambda row: (-row["strongest_abs_correlation"], row["label"]))
    high_pair_count = sum(1 for row in pair_rows if row["band"] == "high")
    moderate_pair_count = sum(1 for row in pair_rows if row["band"] == "moderate")
    low_pair_count = sum(1 for row in pair_rows if row["band"] == "low")

    return {
        "metadata": {
            "source": source,
            "row_count": len(rows),
            "method": "Spearman correlation over image feature columns",
            "high_threshold": REDUNDANCY_HIGH_THRESHOLD,
            "moderate_threshold": REDUNDANCY_MODERATE_THRESHOLD,
        },
        "summary": {
            "feature_count": len(feature_rows),
            "pair_count": len(pair_rows),
            "high_pair_count": high_pair_count,
            "moderate_pair_count": moderate_pair_count,
            "low_pair_count": low_pair_count,
        },
        "features": feature_rows,
        "pairs": pair_rows,
    }


def feature_explorer_source_rows(records: list[dict], feature_by_id: dict[str, dict]) -> tuple[list[dict], str]:
    if FEATURES_PATH.exists():
        rows = read_csv(FEATURES_PATH)
        if rows and all(column in rows[0] for column in IMAGE_FEATURE_COLUMNS):
            return rows, FEATURES_PATH.relative_to(ROOT).as_posix()

    rows = []
    for record in records:
        feature_row = feature_by_id.get(record["icon_id"], {})
        rows.append(
            {
                "icon_id": record["icon_id"],
                "label": record.get("label", ""),
                "set_name": record.get("set_name", ""),
                "normalized_path": record.get("normalized_path", ""),
                **{column: feature_row.get(column, "") for column in IMAGE_FEATURE_COLUMNS},
            }
        )
    return rows, "analysis_dashboard_sample"


def explorer_icon_example(row: dict, value: float, source: str) -> dict:
    normalized_path = row.get("normalized_path", "")
    if source != "analysis_dashboard_sample" and normalized_path:
        normalized_path = relative_to_dashboard(ROOT / normalized_path)
    return {
        "icon_id": row.get("icon_id", ""),
        "label": row.get("label", ""),
        "set_name": row.get("set_name", ""),
        "normalized_path": normalized_path,
        "value": round(float(value), 6),
    }


def strongest_signed_partners(feature_id: str, pairs: list[dict]) -> dict:
    positive = None
    negative = None
    for pair in pairs:
        if pair["feature_a"] == feature_id:
            partner_id = pair["feature_b"]
            partner_label = pair["feature_b_label"]
            partner_group = pair["feature_b_group_title"]
        elif pair["feature_b"] == feature_id:
            partner_id = pair["feature_a"]
            partner_label = pair["feature_a_label"]
            partner_group = pair["feature_a_group_title"]
        else:
            continue

        partner = {
            "feature_id": partner_id,
            "label": partner_label,
            "group_title": partner_group,
            "correlation": pair["correlation"],
            "abs_correlation": pair["abs_correlation"],
            "band": pair["band"],
            "pair_count": pair["pair_count"],
        }
        if pair["correlation"] > 0 and (positive is None or pair["correlation"] > positive["correlation"]):
            positive = partner
        if pair["correlation"] < 0 and (negative is None or pair["correlation"] < negative["correlation"]):
            negative = partner
    return {"positive": positive, "negative": negative}


def feature_explorer_representative_ids() -> list[str]:
    """Return Feature Groups representatives in their displayed family order."""

    return [section["representative_feature_id"] for section in image_feature_sections()]


def build_feature_explorer(records: list[dict], feature_by_id: dict[str, dict], feature_review: dict) -> dict:
    rows, source = feature_explorer_source_rows(records, feature_by_id)
    metadata = feature_metadata_by_id()
    review_by_id = {
        row["feature_id"]: row
        for row in feature_review.get("features", [])
    }
    selected_feature_ids = feature_explorer_representative_ids()
    missing_review_ids = [
        feature_id for feature_id in selected_feature_ids if feature_id not in review_by_id
    ]
    if missing_review_ids:
        raise ValueError(
            "Feature Values representatives are missing from Feature Review: "
            + ", ".join(missing_review_ids)
        )
    features = []
    for feature_id in selected_feature_ids:
        entries = [
            (row, finite_float(row.get(feature_id)))
            for row in rows
            if math.isfinite(finite_float(row.get(feature_id)))
        ]
        values = np.array([value for _, value in entries], dtype=float)
        if len(values):
            mean = float(values.mean())
            median = float(np.median(values))
            variance = float(values.var())
            std = float(values.std())
            min_value = float(values.min())
            max_value = float(values.max())
            low_examples = sorted(entries, key=lambda item: (item[1], item[0].get("label", "")))[:6]
            mean_examples = sorted(entries, key=lambda item: (abs(item[1] - mean), item[0].get("label", "")))[:6]
            high_examples = sorted(entries, key=lambda item: (-item[1], item[0].get("label", "")))[:6]
        else:
            mean = median = variance = std = min_value = max_value = 0.0
            low_examples = mean_examples = high_examples = []

        feature_meta = metadata.get(feature_id, {})
        selection = review_by_id[feature_id]
        partners = strongest_signed_partners(feature_id, feature_review.get("pairs", []))
        features.append(
            {
                "feature_id": feature_id,
                "label": feature_meta.get("label", FEATURE_LABELS.get(feature_id, title_case(feature_id))),
                "group": feature_meta.get("group", ""),
                "group_title": feature_meta.get("group_title", ""),
                "meaning": feature_meta.get("meaning", ""),
                "min": round(min_value, 6),
                "max": round(max_value, 6),
                "mean": round(mean, 6),
                "median": round(median, 6),
                "variance": round(variance, 6),
                "std": round(std, 6),
                "valid_count": int(len(values)),
                "missing_count": int(len(rows) - len(values)),
                "examples": {
                    "low": [explorer_icon_example(row, value, source) for row, value in low_examples],
                    "mean": [explorer_icon_example(row, value, source) for row, value in mean_examples],
                    "high": [explorer_icon_example(row, value, source) for row, value in high_examples],
                },
                "correlations": partners,
                "selection": {
                    "basis": "Feature Groups representative",
                    "strongest_abs_spearman": selection["strongest_abs_correlation"],
                    "strongest_partner": selection["strongest_partner"],
                    "strongest_partner_label": selection["strongest_partner_label"],
                },
            }
        )

    return {
        "metadata": {
            "source": source,
            "row_count": len(rows),
            "examples_per_band": 6,
            "feature_count": len(features),
            "features_per_family_limit": 1,
            "selection_method": "Exactly the seven representative features used by Feature Groups, in the same family order.",
            "method": "Low, nearest-mean, and high feature-value examples with Spearman partners",
        },
        "features": features,
    }


def apply_group_weights(matrix: np.ndarray, columns: list[str], groups: list[list[str]]) -> np.ndarray:
    weighted = matrix.copy()
    column_index = {column: index for index, column in enumerate(columns)}
    for group in groups:
        indices = [column_index[column] for column in group if column in column_index]
        if not indices:
            continue
        weighted[:, indices] /= math.sqrt(len(indices))
    return weighted


def one_hot(rows: list[dict], column: str, prefix: str, max_values: int | None = None) -> tuple[np.ndarray, list[str]]:
    counts = Counter(row.get(column, "") or "missing" for row in rows)
    values = [value for value, _ in counts.most_common(max_values)]
    matrix = np.zeros((len(rows), len(values)), dtype=float)
    index = {value: idx for idx, value in enumerate(values)}
    for row_idx, row in enumerate(rows):
        value = row.get(column, "") or "missing"
        if value in index:
            matrix[row_idx, index[value]] = 1.0
    return matrix, [f"{prefix}:{value}" for value in values]


def token_features(rows: list[dict], max_tokens: int = 80) -> tuple[np.ndarray, list[str]]:
    counts: Counter[str] = Counter()
    row_tokens = []
    for row in rows:
        tokens = sorted(set((row.get("metadata_tokens") or "").split()))
        row_tokens.append(tokens)
        counts.update(tokens)
    vocabulary = [token for token, _ in counts.most_common(max_tokens)]
    index = {token: idx for idx, token in enumerate(vocabulary)}
    matrix = np.zeros((len(rows), len(vocabulary)), dtype=float)
    for row_idx, tokens in enumerate(row_tokens):
        for token in tokens:
            if token in index:
                matrix[row_idx, index[token]] = 1.0
    return matrix, [f"token:{token}" for token in vocabulary]


def feature_matrices(rows: list[dict], feature_by_id: dict[str, dict]) -> dict[str, dict]:
    image_columns = active_image_feature_columns()
    image = np.array(
        [[to_float(feature_by_id[row["icon_id"]].get(column)) for column in image_columns] for row in rows],
        dtype=float,
    )
    image_scaled, image_means, image_stds = standardize(image)
    image_scaled = apply_group_weights(image_scaled, image_columns, active_image_feature_groups())

    set_matrix, set_columns = one_hot(rows, "set_name", "set")
    token_matrix, token_columns = token_features(rows)
    mcdougall = np.array(
        [[to_float(row.get(column)) for column in MCDOUGALL_NUMERIC_COLUMNS] for row in rows],
        dtype=float,
    )
    mcdougall_scaled, _, _ = standardize(mcdougall)

    metadata_matrix = np.hstack([set_matrix, token_matrix, mcdougall_scaled])
    metadata_columns = set_columns + token_columns + MCDOUGALL_NUMERIC_COLUMNS
    combined_matrix = np.hstack([image_scaled, metadata_matrix])

    return {
        "image": {
            "matrix": image_scaled,
            "columns": image_columns,
            "raw_matrix": image,
            "means": image_means,
            "stds": image_stds,
        },
        "metadata": {
            "matrix": metadata_matrix,
            "columns": metadata_columns,
        },
        "combined": {
            "matrix": combined_matrix,
            "columns": image_columns + metadata_columns,
        },
    }


def representative_indices(matrix: np.ndarray, labels: np.ndarray, limit: int = 8) -> dict[int, list[int]]:
    representatives: dict[int, list[int]] = {}
    for cluster in sorted(set(labels.tolist())):
        indices = np.where(labels == cluster)[0]
        center = matrix[indices].mean(axis=0)
        distances = np.linalg.norm(matrix[indices] - center, axis=1)
        ordered = indices[np.argsort(distances)[:limit]]
        representatives[int(cluster)] = [int(index) for index in ordered]
    return representatives


def cluster_summary(rows: list[dict], matrix: np.ndarray, labels: np.ndarray, method: str, variant: str, k: int) -> list[dict]:
    reps = representative_indices(matrix, labels)
    summaries = []
    for cluster in sorted(set(labels.tolist())):
        indices = [idx for idx, label in enumerate(labels) if label == cluster]
        subset = [rows[idx] for idx in indices]
        set_counts = Counter(row["set_name"] for row in subset).most_common(5)
        summaries.append(
            {
                "method": method,
                "variant": variant,
                "k": k,
                "cluster": int(cluster),
                "size": len(indices),
                "top_sets": json.dumps(set_counts, ensure_ascii=False),
                "representative_icon_ids": " ".join(rows[idx]["icon_id"] for idx in reps[int(cluster)]),
            }
        )
    return summaries


def build_clusters(rows: list[dict], matrices: dict[str, dict]) -> tuple[dict, list[dict], list[dict]]:
    clusters: dict[str, dict] = {}
    assignment_rows = []
    summary_rows = []
    for variant in FEATURE_VARIANTS:
        matrix = matrices[variant]["matrix"]
        clusters[variant] = {"pca": pca_2d(matrix).round(6).tolist(), "kmeans": {}, "hierarchical": {}}

        for k in K_VALUES:
            labels, centers = kmeans(matrix, k, RANDOM_SEED)
            score = silhouette_proxy(matrix, labels, centers)
            clusters[variant]["kmeans"][str(k)] = {
                "labels": labels.astype(int).tolist(),
                "score": round(score, 6),
                "representatives": representative_indices(matrix, labels),
            }
            for idx, row in enumerate(rows):
                assignment_rows.append(
                    {
                        "icon_id": row["icon_id"],
                        "method": "kmeans",
                        "variant": variant,
                        "k": k,
                        "cluster": int(labels[idx]),
                        "quality_score": round(score, 6),
                    }
                )
            summary_rows.extend(cluster_summary(rows, matrix, labels, "kmeans", variant, k))

        hierarchical = hierarchical_single_linkage_labels(matrix, K_VALUES)
        for k, labels in hierarchical.items():
            clusters[variant]["hierarchical"][str(k)] = {
                "labels": labels.astype(int).tolist(),
                "representatives": representative_indices(matrix, labels),
            }
            for idx, row in enumerate(rows):
                assignment_rows.append(
                    {
                        "icon_id": row["icon_id"],
                        "method": "hierarchical",
                        "variant": variant,
                        "k": k,
                        "cluster": int(labels[idx]),
                        "quality_score": "",
                    }
                )
            summary_rows.extend(cluster_summary(rows, matrix, labels, "hierarchical", variant, k))
    return clusters, assignment_rows, summary_rows


def write_feature_tables(rows: list[dict], feature_by_id: dict[str, dict], matrices: dict[str, dict]) -> None:
    image_rows = []
    metadata_rows = []
    combined_rows = []
    for index, row in enumerate(rows):
        base = {column: row.get(column, "") for column in METADATA_COLUMNS}
        image_rows.append(
            base | {column: feature_by_id[row["icon_id"]].get(column, "") for column in IMAGE_FEATURE_COLUMNS}
        )
        metadata_rows.append(
            base
            | {
                column: round(float(matrices["metadata"]["matrix"][index, col_idx]), 6)
                for col_idx, column in enumerate(matrices["metadata"]["columns"])
            }
        )
        combined_rows.append(
            base
            | {
                column: round(float(matrices["combined"]["matrix"][index, col_idx]), 6)
                for col_idx, column in enumerate(matrices["combined"]["columns"])
            }
        )
    write_rows(OUTPUT_DIR / "features_image.csv", image_rows)
    write_rows(OUTPUT_DIR / "features_metadata.csv", metadata_rows)
    write_rows(OUTPUT_DIR / "features_combined.csv", combined_rows)


def build_feature_group_records(feature_rows: list[dict]) -> list[dict]:
    """Build the certain-mask payload used by the Feature Groups pilot gallery."""
    representative_columns = [
        section["representative_feature_id"] for section in image_feature_sections()
    ]
    value_columns = list(
        dict.fromkeys(
            [
                *representative_columns,
                "is_monochrome",
                "orientation_confidence_v2",
                "red_pixel_ratio_v2",
                "strict_red_flag_v2",
            ]
        )
    )
    records = []
    for row in feature_rows:
        normalized_path = row.get("normalized_path", "")
        mask_is_uncertain = str(row.get("mask_is_uncertain", "")).strip().lower() == "true"
        if not row.get("icon_id") or not normalized_path or mask_is_uncertain:
            continue
        image_features = {}
        for column in value_columns:
            value = to_optional_float(row.get(column))
            image_features[column] = round(value, 6) if value is not None else None
        records.append(
            {
                "icon_id": row["icon_id"],
                "label": row.get("label", ""),
                "set_id": row.get("set_id", ""),
                "set_name": row.get("set_name", ""),
                "normalized_path": relative_to_dashboard(ROOT / normalized_path),
                "mask_mode": row.get("mask_mode", ""),
                "mask_coverage": round(to_float(row.get("mask_coverage")), 6),
                "mask_border_contact": round(to_float(row.get("mask_border_contact")), 6),
                "mask_confidence": round(to_float(row.get("mask_confidence")), 6),
                "mask_is_uncertain": False,
                "image_features": image_features,
            }
        )
    return records


def write_dashboard_data(rows: list[dict], feature_by_id: dict[str, dict], matrices: dict[str, dict], clusters: dict) -> None:
    records = []
    for row in rows:
        image_features = {
            column: round(to_float(feature_by_id[row["icon_id"]].get(column)), 6)
            for column in IMAGE_FEATURE_COLUMNS
        }
        mcdougall = {column: row.get(column, "") for column in MCDOUGALL_NUMERIC_COLUMNS}
        mcdougall["mcdougall_common_response"] = row.get("mcdougall_common_response", "")
        records.append(
            {
                "icon_id": row["icon_id"],
                "label": row.get("label", ""),
                "set_id": row.get("set_id", ""),
                "set_name": row.get("set_name", ""),
                "format": row.get("format", ""),
                "normalized_path": relative_to_dashboard(ROOT / row.get("normalized_path", "")),
                "metadata_tokens": row.get("metadata_tokens", ""),
                "image_features": image_features,
                "mcdougall": mcdougall,
            }
        )

    feature_review = build_feature_review(feature_by_id)
    feature_group_source_rows, feature_group_source = feature_review_source_rows(feature_by_id)
    feature_group_records = build_feature_group_records(feature_group_source_rows)
    data = {
        "metadata": {
            "feature_schema_version": feature_registry.FEATURE_SCHEMA_VERSION,
            "analysis_feature_preset": feature_registry.ANALYSIS_FEATURE_PRESET,
            "orientation_confidence_threshold": feature_registry.ORIENTATION_CONFIDENCE_THRESHOLD,
            "generated_from": DATASET_PATH.relative_to(ROOT).as_posix(),
            "row_count": len(records),
            "per_set_sample_size": PER_SET_SAMPLE_SIZE,
            "feature_group_sample_size": FEATURE_GROUP_SAMPLE_SIZE,
            "feature_group_sampling": "equal_width_stratified_random",
            "feature_group_bin_count": FEATURE_GROUP_BIN_COUNT,
            "feature_group_samples_per_bin": FEATURE_GROUP_SAMPLES_PER_BIN,
            "feature_group_excludes_uncertain_masks": True,
            "feature_group_source": feature_group_source,
            "feature_group_source_row_count": len(feature_group_records),
            "random_seed": RANDOM_SEED,
            "k_values": list(K_VALUES),
            "primary_k": PRIMARY_K,
            "feature_variants": list(FEATURE_VARIANTS),
            "image_feature_columns": matrices["image"]["columns"],
            "raw_image_feature_columns": IMAGE_FEATURE_COLUMNS,
            "excluded_image_features": sorted(EXCLUDED_IMAGE_FEATURES),
            "excluded_image_feature_reasons": EXCLUDED_IMAGE_FEATURE_REASONS,
            "image_feature_groups": {
                extractor.name: list(extractor.columns) for extractor in extract_icon_features.FEATURE_EXTRACTORS
            },
            "image_feature_sections": image_feature_sections(),
            "mcdougall_numeric_columns": MCDOUGALL_NUMERIC_COLUMNS,
        },
        "records": records,
        "feature_group_records": feature_group_records,
        "feature_columns": {variant: matrices[variant]["columns"] for variant in FEATURE_VARIANTS},
        "clusters": clusters,
        "feature_review": feature_review,
        "feature_explorer": build_feature_explorer(records, feature_by_id, feature_review),
    }
    (OUTPUT_DIR / "dashboard_data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def relative_to_dashboard(path: Path) -> str:
    return Path(os.path.relpath(path, OUTPUT_DIR)).as_posix()


def write_index_html() -> None:
    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analysis Icon Clustering Dashboard</title>
  <script src="assets/plotly.min.js"></script>
  <style>
    :root {{ color-scheme: light; --border: #d8dde6; --muted: #5d6675; --panel: #f7f8fb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18202f; background: white; }}
    header {{ padding: 10px 18px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 18px; }}
    h1 {{ font-size: 18px; margin: 0; font-weight: 650; }}
    header span {{ color: var(--muted); font-size: 13px; }}
    .tab-nav {{ display: flex; gap: 6px; margin-left: auto; }}
    .tab-nav button {{ font-size: 13px; padding: 6px 10px; }}
    .tab-nav button.active {{ background: #18202f; color: white; border-color: #18202f; }}
    .view {{ display: none; }}
    .view.active {{ display: block; }}
    #clusteringView.active {{ display: grid; grid-template-columns: 300px minmax(520px, 1fr) 330px; min-height: calc(100vh - 52px); }}
    aside {{ border-right: 1px solid var(--border); padding: 14px; overflow: auto; max-height: calc(100vh - 52px); }}
    aside.right {{ border-left: 1px solid var(--border); border-right: 0; }}
    section.control {{ margin-bottom: 18px; }}
    h2 {{ font-size: 13px; margin: 0 0 8px; text-transform: uppercase; color: #3d4656; letter-spacing: .04em; }}
    label {{ display: block; font-size: 13px; margin: 7px 0; }}
    select, input[type="range"], input[type="search"] {{ width: 100%; }}
    select, input[type="search"] {{ min-height: 30px; border: 1px solid var(--border); border-radius: 6px; background: white; padding: 4px 6px; }}
    button {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 6px 9px; color: #18202f; cursor: pointer; }}
    button:hover {{ background: var(--panel); }}
    .button-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
    .selected-pills {{ display: flex; gap: 5px; flex-wrap: wrap; margin: 6px 0 10px; min-height: 20px; }}
    .filter-pill {{ display: inline-flex; align-items: center; gap: 5px; max-width: 100%; padding: 3px 7px; border: 1px solid #cbd2de; border-radius: 999px; background: #eef2f7; font-size: 12px; color: #18202f; }}
    .filter-pill button {{ border: 0; background: transparent; padding: 0; width: 16px; height: 16px; line-height: 14px; font-size: 14px; color: #4d5665; }}
    .filter-pill button:hover {{ background: #dde3ec; border-radius: 999px; }}
    .checklist {{ display: grid; gap: 8px; }}
    .preset-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }}
    .feature-section {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 8px; }}
    .feature-head {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
    .feature-head b {{ font-size: 13px; }}
    .feature-description {{ color: var(--muted); font-size: 12px; line-height: 1.35; margin: 4px 0 6px; }}
    .feature-interpretation {{ color: #3d4656; font-size: 12px; line-height: 1.35; margin: 6px 0 8px; padding: 6px 7px; border-left: 3px solid #d8dde6; background: #fbfcfe; }}
    .feature-interpretation div + div {{ margin-top: 3px; }}
    .feature-interpretation b {{ font-weight: 650; }}
    .feature-actions {{ display: flex; gap: 4px; flex-shrink: 0; }}
    .feature-actions button, .preset-row button {{ padding: 3px 6px; font-size: 12px; }}
    .feature-list {{ max-height: 150px; overflow: auto; border-top: 1px solid #edf0f4; padding-top: 4px; }}
    .feature-list label {{ margin: 4px 0; line-height: 1.3; }}
    .feature-choice {{ position: relative; display: flex; align-items: flex-start; gap: 6px; padding: 3px 4px; border-radius: 4px; }}
    .feature-choice:hover, .feature-choice:focus-within {{ background: #f3f5f9; }}
    .feature-tooltip {{ display: none; position: fixed; z-index: 30; width: 280px; padding: 9px 10px; border-radius: 6px; background: #18202f; color: white; font-size: 12px; line-height: 1.35; box-shadow: 0 8px 24px rgba(24,32,47,.22); pointer-events: none; }}
    .feature-tooltip b {{ display: block; font-size: 13px; margin-bottom: 4px; }}
    .feature-tooltip .tooltip-section {{ color: #c8d2e2; margin-bottom: 5px; }}
    .feature-tooltip .tooltip-label {{ color: #c8d2e2; margin-top: 7px; }}
    .method-note {{ margin-top: 5px; font-size: 12px; line-height: 1.35; color: var(--muted); }}
    .plot-wrap {{ padding: 10px; min-width: 0; }}
    #scatter {{ width: 100%; height: calc(100vh - 76px); }}
    #hoverPreview {{ position: fixed; z-index: 20; display: none; pointer-events: none; max-width: 360px; max-height: calc(100vh - 16px); overflow: hidden; padding: 8px 10px; border-radius: 0; background: #a000a8; color: white; box-shadow: none; font-size: 18px; line-height: 1.28; }}
    #hoverPreview img {{ width: 84px; height: 84px; object-fit: contain; border: 1px solid rgba(255,255,255,.65); background: white; margin: 8px 10px 2px 0; vertical-align: top; }}
    #hoverPreview b {{ font-size: 18px; }}
    #hoverPreview .hover-grid {{ display: grid; grid-template-columns: 94px minmax(0, 1fr); align-items: start; gap: 0; margin-bottom: 4px; }}
    #hoverPreview .hover-meta {{ min-width: 0; }}
    #hoverPreview .hover-features {{ clear: both; }}
    #hoverPreview .feature-group-detail h4 {{ color: white; }}
    #hoverPreview .feature-group-detail p, #hoverPreview .muted {{ color: rgba(255,255,255,.82); }}
    #hoverPreview table {{ color: white; }}
    #hoverPreview td {{ border-bottom: 1px solid rgba(255,255,255,.42); }}
    #hoverPreview td:last-child {{ color: white; font-variant-numeric: tabular-nums; }}
    .detail-img {{ width: 96px; height: 96px; object-fit: contain; border: 1px solid var(--border); background: white; }}
    .muted {{ color: var(--muted); }}
    .sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }}
    .pill {{ display: inline-block; padding: 2px 6px; border: 1px solid var(--border); border-radius: 999px; margin: 2px; font-size: 12px; background: var(--panel); }}
    .summary-cluster {{ border: 1px solid var(--border); border-radius: 8px; margin: 8px 0; background: white; overflow: hidden; }}
    .summary-cluster summary {{ cursor: pointer; padding: 8px; list-style-position: inside; }}
    .summary-cluster summary:hover {{ background: var(--panel); }}
    .summary-cluster[open] summary {{ border-bottom: 1px solid var(--border); background: #fbfcfe; }}
    .summary-details {{ padding: 8px; }}
    .summary-explain {{ margin-top: 4px; font-size: 12px; color: #3d4656; }}
    .rep-icons {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr)); gap: 8px; margin-top: 8px; }}
    .rep-icon {{ min-width: 0; }}
    .rep-icon img {{ width: 72px; height: 72px; object-fit: contain; border: 1px solid var(--border); background: white; display: block; }}
    .rep-icon span {{ display: block; margin-top: 3px; font-size: 11px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .feature-group-detail {{ margin: 10px 0; }}
    .feature-group-detail h4 {{ font-size: 13px; margin: 0 0 2px; }}
    .feature-group-detail p {{ margin: 0 0 4px; font-size: 12px; color: var(--muted); line-height: 1.35; }}
    .feature-group-detail .family-reading {{ color: #3d4656; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    td {{ border-bottom: 1px solid #edf0f4; padding: 4px 0; vertical-align: top; }}
    td:last-child {{ text-align: right; color: #334; }}
    .feature-review, .feature-explorer, .feature-groups {{ padding: 16px 18px 24px; }}
    .review-toolbar, .explorer-toolbar {{ display: flex; align-items: end; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }}
    .review-toolbar label, .explorer-toolbar label {{ min-width: 180px; margin: 0; }}
    .explorer-toolbar label:nth-child(2) {{ min-width: 240px; }}
    .explorer-toolbar label:nth-child(3) {{ min-width: 280px; flex: 1; }}
    .feature-groups-header {{ max-width: 980px; margin-bottom: 16px; }}
    .feature-groups-header h2 {{ margin: 0 0 6px; font-size: 20px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .feature-groups-header p {{ margin: 0; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .feature-groups-content {{ display: grid; gap: 14px; max-width: 1280px; }}
    .feature-family-overview {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 14px; }}
    .feature-family-overview h2 {{ margin: 0 0 6px; font-size: 18px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .feature-family-overview p {{ margin: 0 0 10px; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .family-overview-table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 6px; }}
    .family-overview-table {{ min-width: 760px; }}
    .family-overview-table th {{ background: #f4f6fa; border-bottom: 1px solid var(--border); padding: 7px 8px; text-align: left; font-size: 12px; color: #3d4656; }}
    .family-overview-table td {{ padding: 10px 8px; text-align: left; vertical-align: top; font-size: 13px; line-height: 1.45; }}
    .family-overview-table td:last-child {{ text-align: left; color: #334; }}
    .family-overview-table b {{ color: #18202f; }}
    .family-detail-button {{ white-space: nowrap; padding: 5px 9px; font-size: 12px; }}
    .family-detail-modal {{ position: fixed; inset: 0; z-index: 60; display: none; background: white; }}
    .family-detail-modal.open {{ display: grid; animation: family-backdrop-in .16s ease-out; }}
    .family-detail-dialog {{ width: 100vw; height: 100vh; height: 100dvh; min-width: 0; overflow: hidden; display: grid; grid-template-rows: auto auto minmax(0, 1fr); border: 0; border-radius: 0; background: white; box-shadow: none; animation: family-dialog-in .2s ease-out; }}
    .family-detail-header {{ display: flex; align-items: start; justify-content: space-between; gap: 20px; padding: 18px 20px 14px; border-bottom: 1px solid var(--border); }}
    .family-detail-header h2 {{ margin: 0 0 5px; font-size: 20px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .family-detail-header p {{ margin: 0; max-width: 780px; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .family-detail-close {{ flex: 0 0 auto; width: 34px; height: 34px; padding: 0; border-radius: 50%; font-size: 20px; line-height: 1; }}
    .family-detail-toolbar {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 11px 20px; border-bottom: 1px solid var(--border); background: #f8fafc; }}
    .family-color-filters {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .family-color-filters button {{ padding: 5px 10px; font-size: 12px; }}
    .family-color-filters button.active {{ border-color: #18202f; background: #18202f; color: white; }}
    .family-detail-actions {{ display: flex; align-items: center; justify-content: flex-end; gap: 10px; }}
    .family-randomize {{ padding: 6px 11px; font-size: 12px; font-weight: 650; }}
    .family-detail-count {{ color: var(--muted); font-size: 12px; white-space: nowrap; }}
    .family-detail-body {{ min-height: 0; overflow: auto; padding: 18px 20px 22px; }}
    .family-selected-feature {{ display: grid; grid-template-columns: minmax(240px, .7fr) minmax(360px, 1.3fr); gap: 18px; margin-bottom: 20px; padding: 16px 18px; border-left: 4px solid #a000a8; background: #faf7fb; }}
    .family-selected-feature h3 {{ margin: 3px 0 5px; font-size: 19px; color: #18202f; }}
    .family-selected-feature p {{ margin: 0; color: #3d4656; font-size: 12px; line-height: 1.5; }}
    .family-selected-feature p + p {{ margin-top: 8px; }}
    .family-selected-kicker {{ color: #7b287f; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    .family-selected-id {{ display: inline-block; margin-top: 8px; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; }}
    .family-selected-evidence {{ padding-left: 18px; border-left: 1px solid #ddd3df; }}
    .family-selected-evidence b {{ color: #18202f; }}
    .family-selected-citation {{ color: #667085 !important; font-style: italic; }}
    .family-icon-heading h3 {{ margin: 0; font-size: 14px; color: #18202f; }}
    .family-icon-heading {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 10px; }}
    .family-sample-average {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 12px; padding: 10px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
    .family-sample-average span, .family-sample-average small {{ display: block; }}
    .family-sample-average span {{ color: #18202f; font-size: 12px; font-weight: 650; }}
    .family-sample-average small {{ margin-top: 2px; color: var(--muted); font-size: 11px; font-weight: 400; }}
    .family-sample-average code {{ color: #18202f; font-size: 19px; font-weight: 700; font-variant-numeric: tabular-nums; }}
    .family-value-quality {{ margin: 0 0 12px; padding: 9px 11px; border: 1px solid #cddfeb; border-radius: 6px; background: #f3f9fd; color: #294b61; font-size: 11px; line-height: 1.45; }}
    .family-value-quality.low-information {{ border-color: #ead7a2; background: #fff9e8; color: #674f12; }}
    .family-value-quality b {{ color: #18202f; }}
    .family-icon-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); gap: 10px; }}
    .family-icon {{ min-width: 0; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: #fbfcfe; }}
    .family-icon.selected {{ border-color: #a000a8; box-shadow: 0 0 0 2px rgba(160,0,168,.12); background: #fffaff; }}
    .family-icon img {{ width: 100%; aspect-ratio: 1; object-fit: contain; display: block; border: 1px solid #e5e9f0; background: white; }}
    .family-icon b, .family-icon span {{ display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .family-icon b {{ margin-top: 6px; font-size: 12px; color: #18202f; }}
    .family-icon span {{ margin-top: 2px; font-size: 10px; color: var(--muted); }}
    .family-icon code {{ display: block; margin-top: 5px; color: #18202f; font-size: 10px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .family-icon-select {{ width: 100%; margin-top: 7px; padding: 5px 7px; font-size: 11px; font-weight: 650; }}
    .family-icon-select[aria-pressed="true"] {{ border-color: #a000a8; background: #a000a8; color: white; }}
    .family-compare-status {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 0 12px; padding: 9px 11px; border: 1px solid #e2d5e4; border-radius: 6px; background: #fffaff; color: #5c2960; font-size: 12px; }}
    .family-compare-status div {{ display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
    .family-compare-status b {{ color: #18202f; }}
    .family-compare-open {{ flex: 0 0 auto; border-color: #a000a8; background: #a000a8; color: white; font-weight: 650; }}
    .comparison-modal {{ position: fixed; inset: 0; z-index: 70; display: none; background: white; }}
    .comparison-modal.open {{ display: grid; animation: family-backdrop-in .16s ease-out; }}
    .comparison-dialog {{ width: 100vw; height: 100vh; height: 100dvh; min-width: 0; overflow: hidden; display: grid; grid-template-rows: auto minmax(0, 1fr); background: white; animation: family-dialog-in .2s ease-out; }}
    .comparison-header {{ display: flex; align-items: start; justify-content: space-between; gap: 20px; padding: 18px 20px 14px; border-bottom: 1px solid var(--border); }}
    .comparison-header h2 {{ margin: 0 0 5px; color: #18202f; font-size: 20px; }}
    .comparison-header p {{ margin: 0; color: #667085; font-size: 12px; }}
    .comparison-close {{ flex: 0 0 auto; width: 34px; height: 34px; padding: 0; border-radius: 50%; font-size: 20px; line-height: 1; }}
    .comparison-body {{ min-height: 0; overflow: auto; padding: 20px; background: #fffaff; }}
    .family-comparison {{ min-height: 100%; }}
    .family-comparison-icons {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }}
    .family-comparison-icon {{ min-width: 0; padding: 8px; border: 1px solid #e2d5e4; border-radius: 6px; background: white; text-align: center; }}
    .family-comparison-icon img {{ width: min(100%, 150px); aspect-ratio: 1; object-fit: contain; border: 1px solid #e5e9f0; background: white; }}
    .family-comparison-icon b, .family-comparison-icon span {{ display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .family-comparison-icon b {{ margin-top: 5px; color: #18202f; font-size: 12px; }}
    .family-comparison-icon span {{ margin-top: 2px; color: var(--muted); font-size: 10px; }}
    .family-comparison-table-wrap {{ overflow-x: auto; border: 1px solid #e2d5e4; border-radius: 6px; background: white; }}
    .family-comparison-table {{ min-width: 620px; }}
    .family-comparison-table th, .family-comparison-table td {{ padding: 8px 9px; border-bottom: 1px solid #eee7ef; text-align: right; font-size: 11px; font-variant-numeric: tabular-nums; }}
    .family-comparison-table th:first-child, .family-comparison-table td:first-child {{ text-align: left; }}
    .family-comparison-table thead th {{ color: #3d4656; background: #faf7fb; }}
    .family-comparison-table tr.current-family td {{ background: #fff2ff; font-weight: 700; }}
    .family-comparison-table tbody tr:last-child td {{ border-bottom: 0; }}
    .mask-warning {{ display: block; margin-top: 5px; color: #8a4b08; font-size: 10px; font-style: normal; font-weight: 650; }}
    .family-icon-empty {{ padding: 28px 12px; border: 1px dashed var(--border); text-align: center; color: var(--muted); font-size: 13px; }}
    @keyframes family-backdrop-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes family-dialog-in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .feature-group-panel {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 14px; }}
    .feature-group-panel h2 {{ margin: 0; font-size: 16px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .feature-group-panel p {{ margin: 7px 0 0; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .feature-group-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 10px; }}
    .feature-group-count {{ flex-shrink: 0; color: var(--muted); font-size: 12px; }}
    .feature-reading-grid {{ display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 10px; margin: 12px 0; }}
    .feature-reading-item {{ border-left: 3px solid #d8dde6; background: #fbfcfe; padding: 8px 9px; font-size: 12px; line-height: 1.4; color: #3d4656; }}
    .feature-reading-item b {{ display: block; margin-bottom: 3px; color: #18202f; }}
    .feature-group-table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 6px; }}
    .feature-group-table {{ min-width: 920px; }}
    .feature-group-table th {{ background: #f4f6fa; border-bottom: 1px solid var(--border); padding: 7px 8px; text-align: left; font-size: 12px; color: #3d4656; }}
    .feature-group-table td {{ padding: 7px 8px; text-align: left; }}
    .feature-group-table td:last-child {{ text-align: left; color: #334; }}
    .feature-id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; color: var(--muted); }}
    .review-summary {{ display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px; }}
    .review-metric {{ border: 1px solid var(--border); border-radius: 6px; padding: 10px; background: #fbfcfe; }}
    .review-metric b {{ display: block; font-size: 22px; margin-bottom: 2px; }}
    .review-metric span {{ color: var(--muted); font-size: 12px; }}
    .review-layout {{ display: grid; grid-template-columns: minmax(560px, 1fr) 340px; gap: 16px; align-items: start; }}
    .review-panel {{ min-width: 0; }}
    .review-panel h2 {{ margin-top: 0; }}
    .review-table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 6px; background: white; margin-bottom: 16px; max-height: 360px; }}
    .review-table {{ min-width: 760px; }}
    .review-table th {{ position: sticky; top: 0; background: #f4f6fa; border-bottom: 1px solid var(--border); padding: 7px 8px; text-align: left; font-size: 12px; color: #3d4656; }}
    .review-table td {{ padding: 6px 8px; text-align: left; }}
    .review-table td:last-child {{ text-align: left; }}
    .review-row-button {{ border: 0; background: transparent; padding: 0; color: #18202f; text-align: left; font-weight: 600; }}
    .review-row-button:hover {{ background: transparent; text-decoration: underline; }}
    .band {{ display: inline-block; min-width: 70px; padding: 2px 6px; border-radius: 999px; font-size: 11px; text-align: center; border: 1px solid var(--border); }}
    .band-high {{ background: #ffe8e1; border-color: #f0b7a6; color: #8d2e16; }}
    .band-moderate {{ background: #fff4d7; border-color: #e6cd86; color: #725300; }}
    .band-low {{ background: #edf7ef; border-color: #b7d9bf; color: #245b31; }}
    .review-detail {{ border: 1px solid var(--border); border-radius: 6px; padding: 12px; background: white; position: sticky; top: 12px; }}
    .review-detail h3 {{ margin: 0 0 4px; font-size: 16px; }}
    .review-detail p {{ font-size: 13px; line-height: 1.4; }}
    .partner-list {{ margin-top: 10px; }}
    .partner-list div {{ display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid #edf0f4; padding: 5px 0; font-size: 12px; }}
    .explorer-content {{ max-width: 1280px; }}
    .explorer-layout {{ display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }}
    .explorer-main, .explorer-side {{ min-width: 0; }}
    .explorer-header {{ margin-bottom: 14px; }}
    .explorer-header h2 {{ margin: 0 0 6px; font-size: 20px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .explorer-header p {{ max-width: 820px; margin: 8px 0 0; color: #3d4656; font-size: 13px; line-height: 1.45; }}
    .explorer-stats {{ display: grid; grid-template-columns: repeat(6, minmax(100px, 1fr)); gap: 8px; margin-bottom: 14px; }}
    .explorer-stat {{ border: 1px solid var(--border); border-radius: 6px; background: #fbfcfe; padding: 8px; min-width: 0; }}
    .explorer-stat b {{ display: block; font-size: 14px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .explorer-stat span {{ color: var(--muted); font-size: 11px; }}
    .example-section {{ margin-bottom: 18px; }}
    .example-section h3 {{ display: flex; align-items: center; gap: 7px; margin: 0 0 8px; font-size: 14px; }}
    .value-band-dot {{ width: 9px; height: 9px; border-radius: 999px; background: #8a94a5; flex: 0 0 auto; }}
    .example-section[data-band="low"] .value-band-dot {{ background: #2f855a; }}
    .example-section[data-band="medium"] .value-band-dot {{ background: #d69e2e; }}
    .example-section[data-band="high"] .value-band-dot {{ background: #c53030; }}
    .example-strip {{ display: grid; grid-template-columns: repeat(6, minmax(120px, 1fr)); gap: 10px; }}
    .example-card {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 8px; min-width: 0; }}
    .example-card img {{ width: 100%; aspect-ratio: 1; object-fit: contain; border: 1px solid #edf0f4; background: white; display: block; }}
    .example-card b {{ display: block; margin-top: 6px; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .example-card span {{ display: block; color: var(--muted); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .example-card code {{ display: block; margin-top: 4px; font-size: 11px; color: #18202f; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .correlation-panel {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 12px; position: sticky; top: 12px; }}
    .correlation-panel h3 {{ margin: 0 0 8px; font-size: 15px; }}
    .correlation-item {{ border-top: 1px solid #edf0f4; padding: 9px 0; }}
    .correlation-item:first-of-type {{ border-top: 0; }}
    .correlation-item span {{ display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }}
    .correlation-item button {{ margin: 3px 0; border: 0; background: transparent; padding: 0; color: #18202f; font-weight: 650; text-align: left; }}
    .correlation-item button:hover {{ background: transparent; text-decoration: underline; }}
    .correlation-item b {{ display: block; font-size: 13px; font-variant-numeric: tabular-nums; }}
    .ai-clustering {{ padding: 18px; }}
    .ai-header {{ display: flex; align-items: start; justify-content: space-between; gap: 18px; margin-bottom: 14px; }}
    .ai-header h2 {{ margin: 0 0 5px; font-size: 20px; text-transform: none; letter-spacing: 0; color: #18202f; }}
    .ai-header p {{ margin: 0; max-width: 780px; color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .ai-run {{ background: #18202f; color: white; border-color: #18202f; font-weight: 650; white-space: nowrap; }}
    .ai-run:disabled {{ opacity: .45; cursor: not-allowed; }}
    .ai-status {{ border: 1px solid var(--border); background: var(--panel); border-radius: 7px; padding: 10px 12px; margin-bottom: 14px; font-size: 13px; }}
    .ai-status[data-kind="stale"] {{ border-color: #d69e2e; background: #fffaf0; }}
    .ai-status[data-kind="error"] {{ border-color: #c53030; background: #fff5f5; }}
    .ai-facts, .ai-metrics {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 8px; margin-bottom: 14px; }}
    .ai-fact {{ border: 1px solid var(--border); border-radius: 6px; padding: 9px; min-width: 0; }}
    .ai-fact span {{ display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; }}
    .ai-fact b {{ display: block; margin-top: 3px; overflow-wrap: anywhere; }}
    .ai-plots {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }}
    .ai-panel {{ border: 1px solid var(--border); border-radius: 7px; overflow: hidden; }}
    .ai-panel h3 {{ margin: 0; padding: 9px 11px; border-bottom: 1px solid var(--border); font-size: 14px; }}
    .ai-plot {{ height: 480px; }}
    .ai-lower {{ display: grid; grid-template-columns: minmax(300px, .8fr) minmax(480px, 1.2fr); gap: 12px; }}
    .ai-table-wrap {{ overflow: auto; }}
    .ai-table th, .ai-table td {{ padding: 7px 8px; border-bottom: 1px solid #edf0f4; text-align: left; }}
    .ai-table th {{ background: var(--panel); font-size: 11px; }}
    .ai-table td:last-child {{ text-align: left; }}
    @media (max-width: 980px) {{
      #clusteringView.active {{ grid-template-columns: 1fr; }}
      aside, aside.right {{ max-height: none; border: 0; border-bottom: 1px solid var(--border); }}
      .review-layout, .explorer-layout {{ grid-template-columns: 1fr; }}
      .review-detail, .correlation-panel {{ position: static; }}
      .feature-reading-grid {{ grid-template-columns: 1fr; }}
      .family-selected-feature {{ grid-template-columns: 1fr; }}
      .family-selected-evidence {{ padding: 12px 0 0; border-top: 1px solid #ddd3df; border-left: 0; }}
      .family-detail-toolbar {{ align-items: start; flex-direction: column; }}
      .family-detail-actions {{ width: 100%; justify-content: space-between; }}
      .explorer-stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .example-strip {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .ai-plots, .ai-lower {{ grid-template-columns: 1fr; }}
      .ai-facts, .ai-metrics {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Analysis Icon Clustering Dashboard</h1>
    <span id="datasetSummary">Loading data...</span>
    <nav class="tab-nav" aria-label="Dashboard views">
      <button type="button" class="active" data-view="clustering">Clustering</button>
      <button type="button" data-view="featureGroups">Feature Groups</button>
      <button type="button" data-view="featureExplorer">Feature Values</button>
      <button type="button" data-view="featureReview">Feature Review</button>
      <button type="button" data-view="aiClustering">AI Clustering</button>
    </nav>
  </header>
  <main id="clusteringView" class="view active">
    <aside>
      <section class="control">
        <h2>Feature Variant</h2>
        <label><select id="variantSelect"></select></label>
      </section>
      <section class="control">
        <h2>Clustering</h2>
        <label>Method<select id="methodSelect"><option value="kmeans">K-Means clustering</option><option value="hierarchical">Hierarchical clustering</option></select></label>
        <div class="method-note" id="methodNote"></div>
        <label>Cluster count<select id="kSelect"></select></label>
        <label>Color by<select id="colorSelect"></select></label>
      </section>
      <section class="control">
        <h2>Image Features</h2>
        <div class="preset-row" id="featurePresets"></div>
        <div class="checklist" id="featureChecks"></div>
      </section>
      <section class="control">
        <h2>Filters</h2>
        <label>Icon sets<select id="setFilter" multiple size="8"></select></label>
        <div class="selected-pills" id="setFilterPills"></div>
        <div class="button-row">
          <button type="button" id="clearSetFilter">Clear sets</button>
          <button type="button" id="resetFilters">Reset filters</button>
        </div>
      </section>
    </aside>
    <div class="plot-wrap"><div id="scatter"></div></div>
    <aside class="right">
      <section class="control">
        <h2>Selected Icon</h2>
        <div id="iconDetail" class="muted">Click a point to inspect an icon.</div>
      </section>
      <section class="control">
        <h2>Cluster Summary</h2>
        <div id="clusterSummary"></div>
      </section>
    </aside>
  </main>
  <section id="featureReviewView" class="view feature-review">
    <div class="review-toolbar">
      <label>Feature ranking<select id="featureReviewSort">
        <option value="redundancy">Strongest redundancy</option>
        <option value="group">Group</option>
        <option value="label">Feature name</option>
      </select></label>
      <label>Pair threshold<select id="featureReviewThreshold">
        <option value="high">High only</option>
        <option value="moderate" selected>Moderate+</option>
        <option value="all">All pairs</option>
      </select></label>
    </div>
    <div class="review-summary" id="featureReviewSummary"></div>
    <div class="review-layout">
      <div class="review-panel">
        <h2>Feature Ranking</h2>
        <div class="review-table-wrap"><table class="review-table" id="featureRankingTable"></table></div>
        <h2>Redundant Feature Pairs</h2>
        <div class="review-table-wrap"><table class="review-table" id="featurePairTable"></table></div>
      </div>
      <aside class="review-detail" id="featureReviewDetail">
        <span class="muted">Select a feature to inspect redundancy evidence.</span>
      </aside>
    </div>
  </section>
  <section id="featureGroupsView" class="view feature-groups">
    <div class="feature-groups-header">
      <h2>Feature Groups</h2>
      <p>Feature groups organize image measurements into qualitative families based on human icon perception. This view is intentionally concise: it shows the study-level family and the features grouped under it.</p>
    </div>
    <div class="feature-groups-content" id="featureGroupsContent">
      <span class="muted">Loading feature groups...</span>
    </div>
  </section>
  <section id="featureExplorerView" class="view feature-explorer">
    <div class="explorer-header">
      <h2>Feature Values</h2>
      <p>Browse the same seven representative features used by Feature Groups and compare icons with low, medium, and high values.</p>
    </div>
    <div class="explorer-toolbar">
      <label>Search feature<input id="featureExplorerSearch" type="search" placeholder="Search by name"></label>
      <label>Feature<select id="featureExplorerFeature"></select></label>
    </div>
    <div class="explorer-content" id="featureExplorerContent">
      <span class="muted">Loading feature examples...</span>
    </div>
  </section>
  <section id="aiClusteringView" class="view ai-clustering">
    <div class="ai-header">
      <div><h2>AI Clustering</h2><p>Compare feature-based clustering with image-embedding clustering for the same seven-family composite sample: up to 20 unique icons from each feature family. Metrics measure agreement only; they do not establish that either result is better.</p></div>
      <button class="ai-run" id="aiRunButton" type="button" disabled>Run AI Clustering</button>
    </div>
    <div class="ai-status" id="aiStatus" aria-live="polite">Checking the local AI service...</div>
    <div class="ai-facts" id="aiFacts"></div>
    <div class="ai-plots">
      <section class="ai-panel"><h3>Current feature-based clustering</h3><div class="ai-plot" id="aiFeatureScatter"></div></section>
      <section class="ai-panel"><h3>AI image-embedding clustering</h3><div class="ai-plot" id="aiEmbeddingScatter"></div></section>
    </div>
    <div class="ai-metrics" id="aiMetrics"></div>
    <div class="ai-lower">
      <section class="ai-panel"><h3>Feature versus AI cross-table</h3><div class="ai-table-wrap" id="aiCrossTable"></div></section>
      <section class="ai-panel"><h3>Recent runs</h3><div class="ai-table-wrap" id="aiRecentRuns"></div></section>
    </div>
  </section>
  <div id="familyDetailModal" class="family-detail-modal" role="presentation" aria-hidden="true">
    <section class="family-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="familyDetailTitle">
      <header class="family-detail-header">
        <div>
          <h2 id="familyDetailTitle">Feature family</h2>
          <p id="familyDetailDescription"></p>
        </div>
        <button class="family-detail-close" id="familyDetailClose" type="button" aria-label="Close detail view">&times;</button>
      </header>
      <div class="family-detail-toolbar">
        <div class="family-color-filters" id="familyColorFilters" aria-label="Filter icons by color treatment"></div>
        <div class="family-detail-actions">
          <span class="family-detail-count" id="familyDetailCount"></span>
          <button class="family-randomize" id="familyRandomize" type="button">Randomize icons</button>
        </div>
      </div>
      <div class="family-detail-body" id="familyDetailBody"></div>
    </section>
  </div>
  <div id="comparisonModal" class="comparison-modal" role="presentation" aria-hidden="true">
    <section class="comparison-dialog" role="dialog" aria-modal="true" aria-labelledby="comparisonTitle">
      <header class="comparison-header">
        <div>
          <h2 id="comparisonTitle">Compare 3 icons</h2>
          <p id="comparisonDescription">Representative values across all seven feature families.</p>
        </div>
        <button class="comparison-close" id="comparisonClose" type="button" aria-label="Close comparison">&times;</button>
      </header>
      <div class="comparison-body" id="comparisonBody"></div>
    </section>
  </div>
  <div id="hoverPreview"></div>
  <script>
    let dashboard = null;
    let selectedIconId = null;
    let activeFamilyId = null;
    let familyColorMode = "all";
    let familyDetailReturnFocus = null;
    let familyComparisonReturnFocus = null;
    let familyComparisonIds = new Set();
    let sharedSampleFamilyId = null;
    let sharedSampleColorMode = "all";
    const familySamples = new Map();
    const representativeFeaturesByFamily = new Map();
    const computedCache = new Map();

    const state = {{
      variant: "image",
      method: "kmeans",
      k: "{PRIMARY_K}",
      color: "cluster",
      activeFeatures: new Set(),
      setFilter: new Set()
    }};
    const reviewState = {{
      view: "clustering",
      group: "all",
      sort: "redundancy",
      threshold: "moderate",
      selectedFeatureId: null
    }};
    const explorerState = {{
      group: "all",
      search: "",
      selectedFeatureId: null
    }};
    const aiState = {{service: null, currentRun: null, stale: true, running: false, error: null, recentRuns: []}};

    fetch("dashboard_data.json").then(r => r.json()).then(data => {{
      dashboard = data;
      initializeRepresentativeFeatures();
      state.activeFeatures = new Set(representativeFeatureIds());
      sharedSampleFamilyId = visibleFeatureSections()[0]?.id || null;
      initializeControls();
      initializeAiClustering();
      render();
    }});

    function initializeControls() {{
      document.getElementById("datasetSummary").textContent =
        `${{dashboard.metadata.row_count}} icons, ${{dashboard.metadata.per_set_sample_size}} random per dataset`;

      installViewTabs();
      fillSelect("variantSelect", dashboard.metadata.feature_variants.map(v => [v, title(v)]), state.variant);
      fillSelect("kSelect", dashboard.metadata.k_values.map(k => [String(k), String(k)]), state.k);
      fillColorSelect("colorSelect", state.color);
      renderMethodNote();

      renderFeatureControls();
      initializeFeatureReviewControls();
      initializeFeatureExplorerControls();
      initializeFamilyDetailControls();

      const sets = unique(dashboard.records.map(r => r.set_name)).sort();
      fillSelect("setFilter", sets.map(v => [v, v]), "", true);
      installToggleMultiSelect("setFilter", "setFilter");

      document.getElementById("variantSelect").addEventListener("change", e => {{ state.variant = e.target.value; render(); }});
      document.getElementById("methodSelect").addEventListener("change", e => {{ state.method = e.target.value; markAiClusteringStale(); renderMethodNote(); render(); }});
      document.getElementById("kSelect").addEventListener("change", e => {{ state.k = e.target.value; markAiClusteringStale(); render(); }});
      document.getElementById("colorSelect").addEventListener("change", e => {{ state.color = e.target.value; render(); }});
      document.getElementById("setFilter").addEventListener("change", e => {{
        state.setFilter = new Set(Array.from(e.target.selectedOptions).map(o => o.value));
        renderFilterPills();
        render();
      }});
      document.getElementById("clearSetFilter").addEventListener("click", () => clearSelectFilter("setFilter", "setFilter"));
      document.getElementById("resetFilters").addEventListener("click", resetFilters);
      renderFilterPills();
      renderFeatureGroups();
      renderFeatureReview();
      renderFeatureExplorer();
    }}

    function installViewTabs() {{
      document.querySelectorAll(".tab-nav button").forEach(button => {{
        button.addEventListener("click", () => activateView(button.dataset.view));
      }});
    }}

    function activateView(view) {{
      reviewState.view = view;
      document.querySelectorAll(".tab-nav button").forEach(item => item.classList.toggle("active", item.dataset.view === view));
      document.getElementById("clusteringView").classList.toggle("active", view === "clustering");
      document.getElementById("featureGroupsView").classList.toggle("active", view === "featureGroups");
      document.getElementById("featureReviewView").classList.toggle("active", view === "featureReview");
      document.getElementById("featureExplorerView").classList.toggle("active", view === "featureExplorer");
      document.getElementById("aiClusteringView").classList.toggle("active", view === "aiClustering");
      hideHoverPreview();
      if (view === "clustering") render();
      if (view === "featureGroups") renderFeatureGroups();
      if (view === "featureReview") renderFeatureReview();
      if (view === "featureExplorer") renderFeatureExplorer();
      if (view === "aiClustering") renderAiClustering();
    }}

    function initializeFeatureReviewControls() {{
      document.getElementById("featureReviewSort").addEventListener("change", event => {{
        reviewState.sort = event.target.value;
        renderFeatureReview();
      }});
      document.getElementById("featureReviewThreshold").addEventListener("change", event => {{
        reviewState.threshold = event.target.value;
        renderFeatureReview();
      }});
    }}

    function initializeFeatureExplorerControls() {{
      document.getElementById("featureExplorerSearch").addEventListener("input", event => {{
        explorerState.search = event.target.value;
        explorerState.selectedFeatureId = null;
        renderFeatureExplorer();
      }});
      document.getElementById("featureExplorerFeature").addEventListener("change", event => {{
        explorerState.selectedFeatureId = event.target.value;
        renderFeatureExplorerDetail();
      }});
    }}

    function renderMethodNote() {{
      const note = document.getElementById("methodNote");
      if (!note) return;
      note.textContent = state.method === "hierarchical"
        ? "Hierarchical clustering builds nearest-neighbor links between icons, then cuts the tree at the selected cluster count."
        : "K-Means clustering groups icons around cluster centers at the selected cluster count.";
    }}

    function featureSections() {{
      return dashboard.metadata.image_feature_sections || [{{
        id: "image",
        title: "Image Features",
        description: "Extracted visual features.",
        features: dashboard.metadata.image_feature_columns.map(feature => ({{
          id: feature,
          label: title(feature),
          group: "image",
          group_title: "Image Features",
          meaning: "Extracted visual feature."
        }}))
      }}];
    }}

    function visibleFeatureSections() {{
      return featureSections().filter(section => section.visible !== false);
    }}

    function allFeatureIds() {{
      return featureSections().flatMap(section => section.features.map(feature => feature.id));
    }}

    function visibleFeatureIds() {{
      return visibleFeatureSections().flatMap(section => section.features.map(feature => feature.id));
    }}

    function clusteringFeatureSections() {{
      return visibleFeatureSections()
        .map(section => ({{
          ...section,
          features: representativeFeature(section) ? [representativeFeature(section)] : []
        }}))
        .filter(section => section.features.length);
    }}

    function clusteringSectionById(sectionId) {{
      return clusteringFeatureSections().find(section => section.id === sectionId);
    }}

    function selectedFeatureIds() {{
      const ordered = representativeFeatureIds().filter(feature => state.activeFeatures.has(feature));
      return ordered;
    }}

    function sectionById(sectionId) {{
      return visibleFeatureSections().find(section => section.id === sectionId);
    }}

    function featureInfo(featureId) {{
      for (const section of featureSections()) {{
        const feature = section.features.find(item => item.id === featureId);
        if (feature) return feature;
      }}
      return {{id: featureId, label: title(featureId), group: "", group_title: "", meaning: ""}};
    }}

    function initializeRepresentativeFeatures() {{
      featureSections().forEach(section => {{
        const configured = section.representative_feature || section.features[0];
        if (configured) representativeFeaturesByFamily.set(section.id, configured.id);
      }});
    }}

    function representativeFeature(section) {{
      const selectedId = representativeFeaturesByFamily.get(section.id);
      return section.features.find(feature => feature.id === selectedId)
        || section.representative_feature
        || section.features[0];
    }}

    function representativeFeatureIds() {{
      return visibleFeatureSections()
        .map(section => representativeFeature(section))
        .filter(Boolean)
        .map(feature => feature.id);
    }}

    function updateRepresentativeFeature(familyId, featureId) {{
      const section = sectionById(familyId);
      if (!section || !section.features.some(feature => feature.id === featureId)) return;
      const previousFeature = representativeFeature(section);
      const wasActiveInClustering = previousFeature && state.activeFeatures.has(previousFeature.id);
      representativeFeaturesByFamily.set(familyId, featureId);
      if (previousFeature) state.activeFeatures.delete(previousFeature.id);
      if (wasActiveInClustering) state.activeFeatures.add(featureId);
      if (previousFeature && state.color === previousFeature.id) state.color = featureId;
      Array.from(familySamples.keys())
        .filter(key => key.startsWith(`${{familyId}}:`))
        .forEach(key => familySamples.delete(key));
      familyComparisonIds.clear();
      computedCache.clear();
      markAiClusteringStale();
      renderFeatureControls();
      fillColorSelect("colorSelect", state.color);
      renderFeatureGroups();
      if (activeFamilyId === familyId) renderFamilyDetail();
      render();
    }}

    function renderFeatureControls() {{
      const presets = document.getElementById("featurePresets");
      const checks = document.getElementById("featureChecks");
      const clusteringSections = clusteringFeatureSections();
      presets.innerHTML = [
        '<button type="button" data-feature-preset="all">All</button>',
        ...clusteringSections.map(section => `<button type="button" data-feature-preset="${{section.id}}">${{escapeHtml(section.title.replace(" Features", ""))}}</button>`)
      ].join("");
      checks.innerHTML = clusteringSections.map(section => `
        <div class="feature-section" data-section-id="${{escapeHtml(section.id)}}">
          <div class="feature-head">
            <b>${{escapeHtml(section.title)}}</b>
            <span class="feature-actions">
              <button type="button" data-feature-action="select" data-section-id="${{escapeHtml(section.id)}}">Select all</button>
              <button type="button" data-feature-action="clear" data-section-id="${{escapeHtml(section.id)}}">Clear</button>
            </span>
          </div>
          <div class="feature-description">${{escapeHtml(section.description)}}</div>
          <div class="feature-interpretation">
            <div><b>Human perception:</b> ${{escapeHtml(section.perception || "This family describes a perceptual visual channel.")}}</div>
            <div><b>Low:</b> ${{escapeHtml(section.low_value || "Lower values mean less of this family signal.")}}</div>
            <div><b>High:</b> ${{escapeHtml(section.high_value || "Higher values mean more of this family signal.")}}</div>
          </div>
          <div class="feature-list">
            ${{section.features.map(feature => `
              <label class="feature-choice" data-feature-id="${{escapeHtml(feature.id)}}" data-feature-label="${{escapeHtml(feature.label)}}" data-feature-group="${{escapeHtml(feature.group_title)}}" data-feature-meaning="${{escapeHtml(feature.meaning)}}" data-feature-visual="${{escapeHtml((feature.visual_categorizations || []).join(", "))}}" data-feature-examples="${{escapeHtml((feature.visual_category_labels || []).join("; "))}}" data-feature-reason="${{escapeHtml(feature.category_reason)}}">
                <input class="feature-toggle" type="checkbox" value="${{escapeHtml(feature.id)}}" data-feature-id="${{escapeHtml(feature.id)}}">
                <span>${{escapeHtml(feature.label)}}</span>
              </label>`).join("")}}
          </div>
        </div>`).join("");

      presets.addEventListener("click", event => {{
        const button = event.target.closest("button[data-feature-preset]");
        if (!button) return;
        const preset = button.dataset.featurePreset;
        const section = clusteringSectionById(preset);
        setActiveFeatures(preset === "all" ? representativeFeatureIds() : section.features.map(feature => feature.id));
      }});

      checks.addEventListener("click", event => {{
        const button = event.target.closest("button[data-feature-action]");
        if (!button) return;
        const section = clusteringSectionById(button.dataset.sectionId);
        if (!section) return;
        const next = new Set(state.activeFeatures);
        section.features.forEach(feature => {{
          if (button.dataset.featureAction === "select") next.add(feature.id);
          if (button.dataset.featureAction === "clear") next.delete(feature.id);
        }});
        setActiveFeatures(Array.from(next));
      }});

      checks.addEventListener("change", event => {{
        if (!event.target.classList.contains("feature-toggle")) return;
        state.activeFeatures = new Set(Array.from(checks.querySelectorAll(".feature-toggle:checked")).map(input => input.value));
        computedCache.clear();
        markAiClusteringStale();
        render();
      }});

      checks.addEventListener("mouseover", event => {{
        const choice = event.target.closest(".feature-choice");
        if (choice) showFeatureTooltip(choice, event);
      }});
      checks.addEventListener("mousemove", event => {{
        if (event.target.closest(".feature-choice")) moveFeatureTooltip(event);
      }});
      checks.addEventListener("mouseout", event => {{
        if (event.target.closest(".feature-choice")) hideFeatureTooltip();
      }});
      checks.addEventListener("focusin", event => {{
        const choice = event.target.closest(".feature-choice");
        if (choice) showFeatureTooltip(choice, null);
      }});
      checks.addEventListener("focusout", hideFeatureTooltip);

      syncFeatureCheckboxes();
    }}

    function showFeatureTooltip(choice, event) {{
      let tooltip = document.getElementById("featureTooltip");
      if (!tooltip) {{
        tooltip = document.createElement("div");
        tooltip.id = "featureTooltip";
        tooltip.className = "feature-tooltip";
        document.body.appendChild(tooltip);
      }}
      tooltip.innerHTML = `
        <b>${{escapeHtml(choice.dataset.featureLabel)}}</b>
        <div class="tooltip-section">${{escapeHtml(choice.dataset.featureGroup)}}</div>
        <div>${{escapeHtml(choice.dataset.featureMeaning)}}</div>
        ${{choice.dataset.featureVisual ? `<div class="tooltip-label">Visual categorization</div><div>${{escapeHtml(choice.dataset.featureVisual)}}</div>` : ""}}
        ${{choice.dataset.featureExamples ? `<div class="tooltip-label">Example labels</div><div>${{escapeHtml(choice.dataset.featureExamples)}}</div>` : ""}}
        <div style="margin-top:6px;">${{escapeHtml(choice.dataset.featureReason)}}</div>`;
      tooltip.style.display = "block";
      if (event) {{
        moveFeatureTooltip(event);
      }} else {{
        const rect = choice.getBoundingClientRect();
        placeFeatureTooltip(rect.right + 12, rect.top);
      }}
    }}

    function moveFeatureTooltip(event) {{
      placeFeatureTooltip(event.clientX + 14, event.clientY + 14);
    }}

    function placeFeatureTooltip(x, y) {{
      const tooltip = document.getElementById("featureTooltip");
      if (!tooltip) return;
      const width = tooltip.offsetWidth || 280;
      const height = tooltip.offsetHeight || 120;
      const left = Math.min(x, window.innerWidth - width - 8);
      const top = Math.min(y, window.innerHeight - height - 8);
      tooltip.style.left = `${{Math.max(8, left)}}px`;
      tooltip.style.top = `${{Math.max(8, top)}}px`;
    }}

    function hideFeatureTooltip() {{
      const tooltip = document.getElementById("featureTooltip");
      if (tooltip) tooltip.style.display = "none";
    }}

    function renderFeatureGroups() {{
      const container = document.getElementById("featureGroupsContent");
      if (!container) return;
      const sections = visibleFeatureSections();
      if (!sections.length) {{
        container.innerHTML = '<span class="muted">No feature group metadata is available.</span>';
        return;
      }}
      const overview = `
        <section class="feature-family-overview">
          <h2>Recommended Feature Families For Analysis</h2>
          <p>For thesis experiments, group the features into interpretable families:</p>
          <div class="family-overview-table-wrap">
            <table class="family-overview-table">
              <thead><tr><th>Human category</th><th>Selected representative feature</th><th><span class="sr-only">Details</span></th></tr></thead>
              <tbody>
                ${{sections.map(section => {{
                  const feature = representativeFeature(section);
                  return `<tr>
                    <td><b>${{escapeHtml(section.human_category || section.title.replace(" Features", ""))}}</b></td>
                    <td>
                      <label class="sr-only" for="familyRepresentative-${{escapeHtml(section.id)}}">Representative feature for ${{escapeHtml(section.title)}}</label>
                      <select class="family-representative-select" id="familyRepresentative-${{escapeHtml(section.id)}}" data-family-id="${{escapeHtml(section.id)}}">
                        ${{section.features.map(option => `<option value="${{escapeHtml(option.id)}}" ${{option.id === feature.id ? "selected" : ""}}>${{escapeHtml(option.label)}} · ${{escapeHtml(option.id)}}</option>`).join("")}}
                      </select>
                    </td>
                    <td><button class="family-detail-button" type="button" data-family-id="${{escapeHtml(section.id)}}">View details</button></td>
                  </tr>`;
                }}).join("")}}
              </tbody>
            </table>
          </div>
        </section>`;
      container.innerHTML = overview;
      container.querySelectorAll(".family-detail-button").forEach(button => {{
        button.addEventListener("click", () => openFamilyDetail(button.dataset.familyId, button));
      }});
      container.querySelectorAll(".family-representative-select").forEach(select => {{
        select.addEventListener("change", () => {{
          const familyId = select.dataset.familyId;
          updateRepresentativeFeature(familyId, select.value);
          const refreshed = document.querySelector(`.family-representative-select[data-family-id="${{CSS.escape(familyId)}}"]`);
          if (refreshed) refreshed.focus();
        }});
      }});
    }}

    function initializeFamilyDetailControls() {{
      const modal = document.getElementById("familyDetailModal");
      document.getElementById("familyDetailClose").addEventListener("click", closeFamilyDetail);
      document.getElementById("comparisonClose").addEventListener("click", closeFamilyComparison);
      document.getElementById("familyRandomize").addEventListener("click", () => {{
        if (!activeFamilyId) return;
        familyComparisonIds.clear();
        replaceFamilySample(activeFamilyId, familyColorMode);
        setSharedClusteringSample(activeFamilyId, familyColorMode);
        renderFamilyDetail();
        document.getElementById("familyRandomize").focus();
      }});
      modal.addEventListener("click", event => {{
        if (event.target === modal) closeFamilyDetail();
      }});
      document.addEventListener("keydown", event => {{
        if (event.key !== "Escape") return;
        if (document.getElementById("comparisonModal").classList.contains("open")) closeFamilyComparison();
        else if (modal.classList.contains("open")) closeFamilyDetail();
      }});
    }}

    function iconColorMode(record) {{
      const features = record.image_features || {{}};
      if (Number(features.strict_red_flag_v2) >= 0.5) return "red";
      if (Number(features.is_monochrome) >= 0.5) return "bw";
      return "colored";
    }}

    function orientationConfidence(record) {{
      const confidence = Number((record.image_features || {{}}).orientation_confidence_v2);
      return Number.isFinite(confidence) ? confidence : 0;
    }}

    function hasDefinedOrientation(record) {{
      const threshold = Number(dashboard.metadata.orientation_confidence_threshold || 0.20);
      return orientationConfidence(record) >= threshold;
    }}

    function representativeValue(record, featureId) {{
      const rawValue = (record.image_features || {{}})[featureId];
      if (rawValue === null || rawValue === undefined || rawValue === "") return null;
      const value = Number(rawValue);
      return Number.isFinite(value) ? value : null;
    }}

    function representativeRecordIsEligible(familyId, record) {{
      const section = visibleFeatureSections().find(item => item.id === familyId);
      if (!section) return false;
      const selectedFeature = representativeFeature(section);
      if (representativeValue(record, selectedFeature.id) === null) return false;
      return selectedFeature.id !== "principal_axis_orientation_v2" || hasDefinedOrientation(record);
    }}

    function familySourceRecords(familyId) {{
      const fullCorpusRecords = dashboard.feature_group_records || [];
      const firstFullCorpusRecord = fullCorpusRecords[0];
      const supportsCurrentRepresentatives = firstFullCorpusRecord
        && representativeFeatureIds().every(featureId =>
          Object.hasOwn(firstFullCorpusRecord.image_features || {{}}, featureId)
        );
      if (supportsCurrentRepresentatives) return fullCorpusRecords;
      return dashboard.records || [];
    }}

    function familyPopulation(familyId, colorMode) {{
      const records = familySourceRecords(familyId);
      return records.filter(record =>
        representativeRecordIsEligible(familyId, record)
        && (colorMode === "all" || iconColorMode(record) === colorMode)
      );
    }}

    function familySampleKey(familyId, colorMode) {{
      return `${{familyId}}:${{colorMode}}`;
    }}

    function setSharedClusteringSample(familyId, colorMode) {{
      sharedSampleFamilyId = familyId;
      sharedSampleColorMode = colorMode;
      selectedIconId = null;
      computedCache.clear();
      markAiClusteringStale();
    }}

    function clusteringRecords() {{
      if (state.variant !== "image" || !sharedSampleFamilyId) return dashboard.records || [];
      return combinedFamilySample(sharedSampleColorMode);
    }}

    function randomSample(records, limit) {{
      const shuffled = records.slice();
      for (let index = 0; index < Math.min(limit, shuffled.length); index += 1) {{
        const swapIndex = index + Math.floor(Math.random() * (shuffled.length - index));
        [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
      }}
      return shuffled.slice(0, limit);
    }}

    function quantile(sortedValues, fraction) {{
      if (!sortedValues.length) return null;
      const position = Math.min(sortedValues.length - 1, Math.max(0, (sortedValues.length - 1) * fraction));
      const lower = Math.floor(position);
      const upper = Math.ceil(position);
      if (lower === upper) return sortedValues[lower];
      return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * (position - lower);
    }}

    function axialMeanDegrees(values) {{
      if (!values.length) return 0;
      const doubled = values.map(value => value * 2 * Math.PI / 180);
      const angle = Math.atan2(
        doubled.reduce((total, value) => total + Math.sin(value), 0),
        doubled.reduce((total, value) => total + Math.cos(value), 0)
      ) / 2 * 180 / Math.PI;
      return (angle + 180) % 180;
    }}

    function axialOffsetDegrees(value, center) {{
      return ((value - center + 270) % 180) - 90;
    }}

    function representativeValueProfile(population, featureId) {{
      const values = population
        .map(record => representativeValue(record, featureId))
        .filter(value => value !== null)
        .sort((left, right) => left - right);
      if (!values.length) return {{count: 0, distinctCount: 0, minimum: null, maximum: null, robustSpan: 0, informative: false}};
      const resolution = featureId === "principal_axis_orientation_v2" ? 1 : 0.001;
      const isOrientation = featureId === "principal_axis_orientation_v2";
      const orientationBinCount = Math.round(180 / resolution);
      const distinctCount = new Set(values.map(value => {{
        const rounded = Math.round((isOrientation ? ((value % 180) + 180) % 180 : value) / resolution);
        return isOrientation ? rounded % orientationBinCount : rounded;
      }})).size;
      let robustSpan = Number(quantile(values, 0.90)) - Number(quantile(values, 0.10));
      let informative = distinctCount >= 3 && robustSpan >= resolution * 2;
      if (isOrientation) {{
        const doubled = values.map(value => value * 2 * Math.PI / 180);
        const meanSin = doubled.reduce((total, value) => total + Math.sin(value), 0) / doubled.length;
        const meanCos = doubled.reduce((total, value) => total + Math.cos(value), 0) / doubled.length;
        robustSpan = 1 - Math.hypot(meanSin, meanCos);
        const twoDegreeAxialDispersion = 1 - Math.cos(4 * Math.PI / 180);
        informative = distinctCount >= 3 && robustSpan >= twoDegreeAxialDispersion;
      }}
      return {{
        count: values.length,
        distinctCount,
        minimum: values[0],
        maximum: values[values.length - 1],
        robustSpan,
        informative,
      }};
    }}

    function drawEqualWidthStratifiedSample(population, featureId) {{
      const binCount = Number(dashboard.metadata.feature_group_bin_count || 10);
      const samplesPerBin = Number(dashboard.metadata.feature_group_samples_per_bin || 2);
      const valuedRecords = population
        .map(record => ({{record, value: representativeValue(record, featureId)}}))
        .filter(item => item.value !== null);
      if (!valuedRecords.length) return [];
      const minimum = Math.min(...valuedRecords.map(item => item.value));
      const maximum = Math.max(...valuedRecords.map(item => item.value));
      const bins = Array.from({{length: binCount}}, () => []);
      if (maximum === minimum) {{
        bins[0] = valuedRecords.map(item => item.record);
      }} else {{
        const width = (maximum - minimum) / binCount;
        valuedRecords.forEach(item => {{
          const bin = Math.min(binCount - 1, Math.floor((item.value - minimum) / width));
          bins[bin].push(item.record);
        }});
      }}
      return bins.flatMap(bin => randomSample(bin, samplesPerBin));
    }}

    function replaceFamilySample(familyId, colorMode) {{
      const usedIconIds = new Set();
      visibleFeatureSections().forEach(section => {{
        if (section.id === familyId) return;
        const sample = familySamples.get(familySampleKey(section.id, colorMode)) || [];
        sample.forEach(record => usedIconIds.add(record.icon_id));
      }});
      const population = familyPopulation(familyId, colorMode)
        .filter(record => !usedIconIds.has(record.icon_id));
      const key = familySampleKey(familyId, colorMode);
      const section = visibleFeatureSections().find(item => item.id === familyId);
      const selectedFeature = representativeFeature(section);
      const sample = drawEqualWidthStratifiedSample(population, selectedFeature.id);
      familySamples.set(key, sample);
      return sample;
    }}

    function currentFamilySample(familyId, colorMode) {{
      const key = familySampleKey(familyId, colorMode);
      return familySamples.get(key) || replaceFamilySample(familyId, colorMode);
    }}

    function combinedFamilySample(colorMode) {{
      const records = visibleFeatureSections()
        .flatMap(section => currentFamilySample(section.id, colorMode));
      const uniqueRecords = new Map(records.map(record => [record.icon_id, record]));
      return Array.from(uniqueRecords.values());
    }}

    function openFamilyDetail(familyId, trigger) {{
      const section = visibleFeatureSections().find(item => item.id === familyId);
      if (!section) return;
      activeFamilyId = familyId;
      setSharedClusteringSample(familyId, familyColorMode);
      familyComparisonIds.clear();
      familyDetailReturnFocus = trigger || document.activeElement;
      const modal = document.getElementById("familyDetailModal");
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      renderFamilyDetail();
      document.getElementById("familyDetailClose").focus();
    }}

    function closeFamilyDetail() {{
      const modal = document.getElementById("familyDetailModal");
      if (!modal.classList.contains("open")) return;
      closeFamilyComparison(false);
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
      activeFamilyId = null;
      if (familyDetailReturnFocus) familyDetailReturnFocus.focus();
    }}

    function openFamilyComparison(trigger) {{
      if (familyComparisonIds.size !== {FEATURE_GROUP_COMPARISON_SIZE}) return;
      familyComparisonReturnFocus = trigger || document.activeElement;
      renderFamilyComparison();
      const modal = document.getElementById("comparisonModal");
      document.getElementById("familyDetailModal").setAttribute("aria-hidden", "true");
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
      document.getElementById("comparisonClose").focus();
    }}

    function closeFamilyComparison(restoreFocus = true) {{
      const modal = document.getElementById("comparisonModal");
      if (!modal.classList.contains("open")) return;
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      const familyModal = document.getElementById("familyDetailModal");
      if (familyModal.classList.contains("open")) familyModal.setAttribute("aria-hidden", "false");
      if (restoreFocus && familyComparisonReturnFocus) familyComparisonReturnFocus.focus();
    }}

    function renderFamilyComparison() {{
      const section = visibleFeatureSections().find(item => item.id === activeFamilyId);
      if (!section) return;
      const sample = currentFamilySample(activeFamilyId, familyColorMode);
      const recordsById = new Map(sample.map(record => [record.icon_id, record]));
      const selectedRecords = Array.from(familyComparisonIds)
        .map(iconId => recordsById.get(iconId))
        .filter(Boolean);
      const orientationThreshold = Number(dashboard.metadata.orientation_confidence_threshold || 0.20);
      const comparisonSections = visibleFeatureSections();
      document.getElementById("comparisonTitle").textContent = `Compare 3 icons · ${{section.title}}`;
      document.getElementById("comparisonDescription").textContent =
        "Representative values across all seven feature families. The active family is highlighted.";
      document.getElementById("comparisonBody").innerHTML = `
        <section class="family-comparison">
          <div class="family-comparison-icons">
            ${{selectedRecords.map(record => `
              <div class="family-comparison-icon">
                <img src="${{escapeHtml(record.normalized_path)}}" alt="" loading="lazy">
                <b title="${{escapeHtml(record.label || record.icon_id)}}">${{escapeHtml(record.label || record.icon_id)}}</b>
                <span title="${{escapeHtml(record.set_name)}}">${{escapeHtml(record.set_name)}}</span>
              </div>`).join("")}}
          </div>
          <div class="family-comparison-table-wrap">
            <table class="family-comparison-table">
              <thead><tr><th>Feature family</th>${{selectedRecords.map(record => `<th>${{escapeHtml(record.label || record.icon_id)}}</th>`).join("")}}</tr></thead>
              <tbody>
                ${{comparisonSections.map(compareSection => {{
                  const compareFeature = representativeFeature(compareSection);
                  const compareIsOrientation = compareFeature.id === "principal_axis_orientation_v2";
                  return `<tr class="${{compareSection.id === activeFamilyId ? "current-family" : ""}}">
                    <td>${{escapeHtml(compareSection.human_category || compareSection.title)}}<br><span class="feature-id">${{escapeHtml(compareFeature.label)}}</span></td>
                    ${{selectedRecords.map(record => {{
                      const value = representativeValue(record, compareFeature.id);
                      if (compareIsOrientation && orientationConfidence(record) < orientationThreshold) return "<td>Undefined</td>";
                      return `<td>${{value !== null ? formatFeatureValue(value) : "—"}}${{compareIsOrientation && value !== null ? "°" : ""}}</td>`;
                    }}).join("")}}
                  </tr>`;
                }}).join("")}}
              </tbody>
            </table>
          </div>
        </section>`;
    }}

    function renderFamilyDetail() {{
      const section = visibleFeatureSections().find(item => item.id === activeFamilyId);
      if (!section) return;
      const selectedFeature = representativeFeature(section);
      const configuredFeature = section.representative_feature || section.features[0];
      const usesConfiguredRepresentative = selectedFeature.id === configuredFeature.id;
      const allRecords = familySourceRecords(activeFamilyId)
        .filter(record => representativeRecordIsEligible(activeFamilyId, record));
      const counts = {{
        all: allRecords.length,
        bw: allRecords.filter(record => iconColorMode(record) === "bw").length,
        red: allRecords.filter(record => iconColorMode(record) === "red").length,
        colored: allRecords.filter(record => iconColorMode(record) === "colored").length,
      }};
      const modes = [["all", "All"], ["bw", "B/W"], ["red", "Red"], ["colored", "Colored"]];
      document.getElementById("familyDetailTitle").textContent = section.title;
      document.getElementById("familyDetailDescription").textContent = section.perception || section.description || "";
      document.getElementById("familyColorFilters").innerHTML = modes.map(([id, label]) => `
        <button type="button" class="${{familyColorMode === id ? "active" : ""}}" data-color-mode="${{id}}" aria-pressed="${{familyColorMode === id}}">${{label}} · ${{counts[id]}}</button>`).join("");
      document.querySelectorAll("#familyColorFilters button").forEach(button => {{
        button.addEventListener("click", () => {{
          familyColorMode = button.dataset.colorMode;
          setSharedClusteringSample(activeFamilyId, familyColorMode);
          familyComparisonIds.clear();
          renderFamilyDetail();
          document.querySelector(`#familyColorFilters [data-color-mode="${{familyColorMode}}"]`).focus();
        }});
      }});
      const population = familyPopulation(activeFamilyId, familyColorMode);
      const isOrientation = selectedFeature.id === "principal_axis_orientation_v2";
      const valueProfile = representativeValueProfile(population, selectedFeature.id);
      const orientationThreshold = Number(dashboard.metadata.orientation_confidence_threshold || 0.20);
      const records = currentFamilySample(activeFamilyId, familyColorMode)
        .slice()
        .sort((left, right) => {{
          if (isOrientation) {{
            const leftDefined = orientationConfidence(left) >= orientationThreshold;
            const rightDefined = orientationConfidence(right) >= orientationThreshold;
            if (leftDefined !== rightDefined) return leftDefined ? -1 : 1;
          }}
          return representativeValue(left, selectedFeature.id) - representativeValue(right, selectedFeature.id);
        }});
      const sampleValues = records
        .filter(record => !isOrientation || orientationConfidence(record) >= orientationThreshold)
        .map(record => representativeValue(record, selectedFeature.id))
        .filter(value => value !== null);
      let sampleAverage = null;
      if (sampleValues.length && isOrientation) {{
        const doubled = sampleValues.map(value => value * 2 * Math.PI / 180);
        const angle = Math.atan2(
          doubled.reduce((total, value) => total + Math.sin(value), 0),
          doubled.reduce((total, value) => total + Math.cos(value), 0)
        ) / 2 * 180 / Math.PI;
        sampleAverage = (angle + 180) % 180;
      }} else if (sampleValues.length) {{
        sampleAverage = sampleValues.reduce((total, value) => total + value, 0) / sampleValues.length;
      }}
      const representedDatasets = new Set(records.map(record => record.set_name || "Unknown dataset")).size;
      document.getElementById("familyDetailCount").textContent =
        `${{records.length}} stratified icons from ${{population.length}} matching · ${{representedDatasets}} datasets`;
      document.getElementById("familyRandomize").disabled = population.length <= records.length;
      const comparisonReady = familyComparisonIds.size === {FEATURE_GROUP_COMPARISON_SIZE};
      const valueQualityNotice = valueProfile.informative
        ? `<div class="family-value-quality"><b>Value-diverse sample.</b> Valid zero and near-zero measurements remain included. The minimum-to-maximum range is split into 10 equal-width bins, with up to 2 icons selected randomly from each bin.</div>`
        : `<div class="family-value-quality low-information"><b>Low information in this cohort.</b> The valid measurements have too little spread for a useful low-to-high comparison. Meaningful zero and near-zero values are retained rather than treated as missing.</div>`;
      const icons = records.length ? `<div class="family-icon-grid">${{records.map(record => {{
        const confidence = orientationConfidence(record);
        const orientationUndefined = isOrientation && confidence < orientationThreshold;
        const isSelected = familyComparisonIds.has(record.icon_id);
        const selectionDisabled = !isSelected && familyComparisonIds.size >= {FEATURE_GROUP_COMPARISON_SIZE};
        const valueLabel = orientationUndefined
          ? `Undefined (confidence ${{formatFeatureValue(confidence)}})`
          : `${{formatFeatureValue(record.image_features[selectedFeature.id])}}${{isOrientation ? `Â° (confidence ${{formatFeatureValue(confidence)}})` : ""}}`;
        const maskWarning = record.mask_is_uncertain
          ? `<em class="mask-warning" title="Mask mode: ${{escapeHtml(record.mask_mode || "unknown")}}; confidence ${{formatFeatureValue(record.mask_confidence)}}">Foreground mask uncertain</em>`
          : "";
        return `
        <article class="family-icon${{isSelected ? " selected" : ""}}">
          <img src="${{escapeHtml(record.normalized_path)}}" alt="${{escapeHtml(record.label || "Icon")}}" loading="lazy">
          <b title="${{escapeHtml(record.label || record.icon_id)}}">${{escapeHtml(record.label || record.icon_id)}}</b>
          <span title="${{escapeHtml(record.set_name)}}">${{escapeHtml(record.set_name)}}</span>
          <code title="${{escapeHtml(selectedFeature.label)}}">Value: ${{valueLabel}}</code>
          ${{maskWarning}}
          <button class="family-icon-select" type="button" data-compare-icon="${{escapeHtml(record.icon_id)}}" aria-pressed="${{isSelected}}" ${{selectionDisabled ? "disabled" : ""}}>${{isSelected ? "Selected" : "Select to compare"}}</button>
        </article>`;
      }}).join("")}}</div>` : '<div class="family-icon-empty">No icons match this color treatment.</div>';
      document.getElementById("familyDetailBody").innerHTML = `
        <section class="family-selected-feature">
          <div>
            <span class="family-selected-kicker">Selected feature Â· active registry</span>
            <h3>${{escapeHtml(selectedFeature.label)}}</h3>
            <p>${{escapeHtml(selectedFeature.meaning || "Extracted image feature.")}}</p>
            <span class="family-selected-id">${{escapeHtml(selectedFeature.id)}}</span>
          </div>
          <div class="family-selected-evidence">
            <p><b>How to read it.</b> ${{escapeHtml(usesConfiguredRepresentative
              ? (section.representative_interpretation || selectedFeature.meaning)
              : selectedFeature.meaning)}}</p>
            <p><b>Why this one.</b> ${{escapeHtml(usesConfiguredRepresentative
              ? (section.representative_rationale || "Selected as the configured representative for this visual family.")
              : "Selected for this browser session to explore how this family measurement changes the clustering.")}}</p>
            <p><b>Evidence.</b> ${{escapeHtml(usesConfiguredRepresentative
              ? (section.representative_evidence || "The literature supports this visual construct; the implementation remains a computational proxy.")
              : "The configured representative remains the documented study default; this session override is exploratory.")}}</p>
            ${{usesConfiguredRepresentative ? `<p class="family-selected-citation">${{escapeHtml(section.representative_citation || "")}}</p>` : ""}}
          </div>
        </section>
        <div class="family-icon-heading"><h3>${{records.length}}-icon pilot sample</h3><span class="muted">Randomly sampled up to 2 per equal-width value bin, then ${{isOrientation ? "placed in angular order from 0Â° to 180Â°; only confidence-defined orientations are shown" : `ordered by ${{escapeHtml(selectedFeature.label.toLowerCase())}}`}}.</span></div>
        ${{valueQualityNotice}}
        <div class="family-sample-average">
          <span>Average of shown icons<small>${{isOrientation ? `Axial circular mean of ${{sampleValues.length}} defined orientations from these ${{records.length}} icons` : `Arithmetic mean ${{escapeHtml(selectedFeature.label.toLowerCase())}} across these ${{sampleValues.length}} icons`}}</small></span>
          <code id="familySampleAverage">${{sampleAverage === null ? "—" : formatFeatureValue(sampleAverage)}}</code>
        </div>
        <div class="family-compare-status" aria-live="polite">
          <div><b>Pick 3 icons to compare</b><span>${{familyComparisonIds.size}} of {FEATURE_GROUP_COMPARISON_SIZE} selected</span></div>
          ${{comparisonReady ? '<button class="family-compare-open" id="familyOpenComparison" type="button">View fullscreen comparison</button>' : ""}}
        </div>
        ${{icons}}`;
      const openComparisonButton = document.getElementById("familyOpenComparison");
      if (openComparisonButton) openComparisonButton.addEventListener("click", () => openFamilyComparison(openComparisonButton));
      document.querySelectorAll("[data-compare-icon]").forEach(button => {{
        button.addEventListener("click", () => {{
          const iconId = button.dataset.compareIcon;
          if (familyComparisonIds.has(iconId)) familyComparisonIds.delete(iconId);
          else if (familyComparisonIds.size < {FEATURE_GROUP_COMPARISON_SIZE}) familyComparisonIds.add(iconId);
          renderFamilyDetail();
          const nextButton = document.querySelector(`[data-compare-icon="${{CSS.escape(iconId)}}"]`);
          if (familyComparisonIds.size === {FEATURE_GROUP_COMPARISON_SIZE}) openFamilyComparison(nextButton);
          else if (nextButton) nextButton.focus();
        }});
      }});
    }}

    function setActiveFeatures(featureIds) {{
      const allowed = new Set(representativeFeatureIds());
      state.activeFeatures = new Set(featureIds.filter(featureId => allowed.has(featureId)));
      syncFeatureCheckboxes();
      computedCache.clear();
      markAiClusteringStale();
      render();
    }}

    function syncFeatureCheckboxes() {{
      document.querySelectorAll(".feature-toggle").forEach(input => {{
        input.checked = state.activeFeatures.has(input.value);
      }});
    }}

    function renderFeatureReview() {{
      const review = dashboard.feature_review;
      if (!review) {{
        document.getElementById("featureReviewSummary").innerHTML = "";
        document.getElementById("featureRankingTable").innerHTML = "";
        document.getElementById("featurePairTable").innerHTML = "";
        document.getElementById("featureReviewDetail").innerHTML = '<span class="muted">No feature review data is available.</span>';
        return;
      }}
      renderFeatureReviewSummary(review);
      const features = filteredReviewFeatures(review);
      const pairs = filteredReviewPairs(review);
      if (!reviewState.selectedFeatureId || !features.some(feature => feature.feature_id === reviewState.selectedFeatureId)) {{
        reviewState.selectedFeatureId = features[0] ? features[0].feature_id : null;
      }}
      renderFeatureRankingTable(features);
      renderFeaturePairTable(pairs);
      renderFeatureReviewDetail(review);
    }}

    function renderFeatureReviewSummary(review) {{
      const summary = review.summary || {{}};
      document.getElementById("featureReviewSummary").innerHTML = [
        ["Features", summary.feature_count || 0],
        ["High redundancy pairs", summary.high_pair_count || 0],
        ["Moderate pairs", summary.moderate_pair_count || 0],
        ["Source rows", (review.metadata || {{}}).row_count || 0]
      ].map(([label, value]) => `<div class="review-metric"><b>${{escapeHtml(value)}}</b><span>${{escapeHtml(label)}}</span></div>`).join("");
    }}

    function filteredReviewFeatures(review) {{
      const sorted = review.features.slice();
      sorted.sort((a, b) => {{
        if (reviewState.sort === "label") return a.label.localeCompare(b.label);
        if (reviewState.sort === "group") return (a.group_title || "").localeCompare(b.group_title || "") || a.label.localeCompare(b.label);
        return Number(b.strongest_abs_correlation || 0) - Number(a.strongest_abs_correlation || 0) || a.label.localeCompare(b.label);
      }});
      return sorted;
    }}

    function filteredReviewPairs(review) {{
      return review.pairs.filter(pair => {{
        if (reviewState.threshold === "high") return pair.band === "high";
        if (reviewState.threshold === "moderate") return pair.band === "high" || pair.band === "moderate";
        return true;
      }});
    }}

    function renderFeatureRankingTable(features) {{
      const table = document.getElementById("featureRankingTable");
      if (!features.length) {{
        table.innerHTML = '<tbody><tr><td class="muted">No features match this filter.</td></tr></tbody>';
        return;
      }}
      const rows = features.map(feature => `
        <tr>
          <td><button class="review-row-button" type="button" data-feature-id="${{escapeHtml(feature.feature_id)}}">${{escapeHtml(feature.label)}}</button></td>
          <td>${{escapeHtml(feature.group_title || "")}}</td>
          <td><span class="band band-${{escapeHtml(feature.redundancy_band)}}">${{escapeHtml(bandLabel(feature.redundancy_band))}}</span></td>
          <td>${{formatNumber(feature.strongest_abs_correlation)}}</td>
          <td>${{escapeHtml(feature.strongest_partner_label || "")}}</td>
          <td>${{formatNumber(feature.std)}}</td>
          <td>${{escapeHtml(feature.missing_count)}}</td>
        </tr>`).join("");
      table.innerHTML = `
        <thead><tr>
          <th>Feature</th><th>Group</th><th>Band</th><th>Strongest |rho|</th><th>Strongest partner</th><th>Std</th><th>Missing</th>
        </tr></thead><tbody>${{rows}}</tbody>`;
      table.querySelectorAll("button[data-feature-id]").forEach(button => {{
        button.addEventListener("click", () => {{
          reviewState.selectedFeatureId = button.dataset.featureId;
          renderFeatureReviewDetail(dashboard.feature_review);
        }});
      }});
    }}

    function renderFeaturePairTable(pairs) {{
      const table = document.getElementById("featurePairTable");
      if (!pairs.length) {{
        table.innerHTML = '<tbody><tr><td class="muted">No feature pairs match this threshold.</td></tr></tbody>';
        return;
      }}
      const rows = pairs.map(pair => `
        <tr>
          <td>${{escapeHtml(pair.feature_a_label)}}</td>
          <td>${{escapeHtml(pair.feature_b_label)}}</td>
          <td><span class="band band-${{escapeHtml(pair.band)}}">${{escapeHtml(bandLabel(pair.band))}}</span></td>
          <td>${{formatSigned(pair.correlation)}}</td>
          <td>${{pair.shared_group ? "Same" : "Different"}}</td>
          <td>${{escapeHtml(pair.pair_count)}}</td>
        </tr>`).join("");
      table.innerHTML = `
        <thead><tr>
          <th>Feature A</th><th>Feature B</th><th>Band</th><th>Spearman rho</th><th>Group</th><th>N</th>
        </tr></thead><tbody>${{rows}}</tbody>`;
    }}

    function renderFeatureReviewDetail(review) {{
      const feature = review.features.find(item => item.feature_id === reviewState.selectedFeatureId);
      const detail = document.getElementById("featureReviewDetail");
      if (!feature) {{
        detail.innerHTML = '<span class="muted">Select a feature to inspect redundancy evidence.</span>';
        return;
      }}
      const partners = review.pairs
        .filter(pair => pair.feature_a === feature.feature_id || pair.feature_b === feature.feature_id)
        .sort((a, b) => Number(b.abs_correlation) - Number(a.abs_correlation))
        .slice(0, 8)
        .map(pair => {{
          const partnerLabel = pair.feature_a === feature.feature_id ? pair.feature_b_label : pair.feature_a_label;
          return `<div><span>${{escapeHtml(partnerLabel)}}</span><b>${{formatSigned(pair.correlation)}}</b></div>`;
        }}).join("");
      detail.innerHTML = `
        <h3>${{escapeHtml(feature.label)}}</h3>
        <span class="pill">${{escapeHtml(feature.group_title || "Image feature")}}</span>
        <span class="band band-${{escapeHtml(feature.redundancy_band)}}">${{escapeHtml(bandLabel(feature.redundancy_band))}}</span>
        <p>${{escapeHtml(feature.meaning || "Extracted image feature.")}}</p>
        <table>
          <tr><td>Strongest absolute correlation</td><td>${{formatNumber(feature.strongest_abs_correlation)}}</td></tr>
          <tr><td>Strongest partner</td><td>${{escapeHtml(feature.strongest_partner_label || "")}}</td></tr>
          <tr><td>Signed correlation</td><td>${{formatSigned(feature.strongest_correlation)}}</td></tr>
          <tr><td>Variance</td><td>${{formatNumber(feature.variance)}}</td></tr>
          <tr><td>Std</td><td>${{formatNumber(feature.std)}}</td></tr>
          <tr><td>Missing values</td><td>${{escapeHtml(feature.missing_count)}}</td></tr>
        </table>
        <div class="partner-list">
          <h2>Top Partners</h2>
          ${{partners || '<span class="muted">No correlation partners available.</span>'}}
        </div>`;
    }}

    function renderFeatureExplorer() {{
      const explorer = dashboard.feature_explorer;
      const container = document.getElementById("featureExplorerContent");
      if (!explorer) {{
        container.innerHTML = '<span class="muted">No feature explorer data is available.</span>';
        return;
      }}
      const features = filteredExplorerFeatures();
      if (!features.length) {{
        explorerState.selectedFeatureId = null;
        renderFeatureExplorerControls(features);
        container.innerHTML = '<span class="muted">No features match this filter.</span>';
        return;
      }}
      if (!explorerState.selectedFeatureId || !features.some(feature => feature.feature_id === explorerState.selectedFeatureId)) {{
        explorerState.selectedFeatureId = features[0].feature_id;
      }}
      renderFeatureExplorerControls(features);
      renderFeatureExplorerDetail();
    }}

    function filteredExplorerFeatures() {{
      const explorer = dashboard.feature_explorer;
      const query = explorerState.search.trim().toLowerCase();
      return (explorer.features || [])
        .filter(feature => !query || `${{feature.label}} ${{feature.feature_id}} ${{feature.group_title}}`.toLowerCase().includes(query))
        .sort((a, b) => (a.group_title || "").localeCompare(b.group_title || "") || a.label.localeCompare(b.label));
    }}

    function renderFeatureExplorerControls(features) {{
      const options = features.map(feature => [feature.feature_id, `${{feature.label}} - ${{feature.group_title || "Image feature"}}`]);
      fillSelect("featureExplorerFeature", options, explorerState.selectedFeatureId || "");
    }}

    function renderFeatureExplorerDetail() {{
      const explorer = dashboard.feature_explorer;
      const feature = (explorer.features || []).find(item => item.feature_id === explorerState.selectedFeatureId);
      const container = document.getElementById("featureExplorerContent");
      if (!feature) {{
        container.innerHTML = '<span class="muted">Select a feature to inspect visual examples.</span>';
        return;
      }}
      const stats = [
        ["Min", feature.min],
        ["Mean", feature.mean],
        ["Max", feature.max],
        ["Variance", feature.variance],
        ["Std", feature.std],
        ["Missing", feature.missing_count]
      ].map(([label, value]) => `<div class="explorer-stat"><b>${{label === "Missing" ? escapeHtml(value) : formatNumber(value)}}</b><span>${{escapeHtml(label)}}</span></div>`).join("");
      container.innerHTML = `
        <div class="explorer-layout">
          <div class="explorer-main">
            <div class="explorer-header">
              <h2>${{escapeHtml(feature.label)}}</h2>
              <span class="pill">${{escapeHtml(feature.group_title || "Image feature")}}</span>
              <p>${{escapeHtml(feature.meaning || "Extracted image feature.")}}</p>
              <p class="muted">${{escapeHtml(feature.selection.basis || "Feature Groups representative")}} · strongest |ρ| ${{formatNumber(feature.selection.strongest_abs_spearman)}}</p>
            </div>
            <div class="explorer-stats">${{stats}}</div>
            ${{exampleSectionHtml("Low Values", feature.examples.low, "Icons with the smallest raw values for this feature.", "low")}}
            ${{exampleSectionHtml("Medium Values", feature.examples.mean, "Icons closest to the average feature value.", "medium")}}
            ${{exampleSectionHtml("High Values", feature.examples.high, "Icons with the largest raw values for this feature.", "high")}}
          </div>
          <aside class="explorer-side">
            <div class="correlation-panel">
              <h3>Correlation Partners</h3>
              <p class="muted">Spearman rho values show how this feature moves with other features.</p>
              ${{correlationPartnerHtml("Strongest positive", feature.correlations.positive)}}
              ${{correlationPartnerHtml("Strongest negative", feature.correlations.negative)}}
            </div>
          </aside>
        </div>`;
      container.querySelectorAll("button[data-explorer-partner]").forEach(button => {{
        button.addEventListener("click", () => openFeatureInExplorer(button.dataset.explorerPartner));
      }});
    }}

    function exampleSectionHtml(titleText, examples, description, band) {{
      const cards = (examples || []).map(example => `
        <div class="example-card">
          <img src="${{escapeHtml(example.normalized_path)}}" alt="">
          <b title="${{escapeHtml(example.label)}}">${{escapeHtml(example.label || example.icon_id)}}</b>
          <span title="${{escapeHtml(example.set_name)}}">${{escapeHtml(example.set_name || "Unknown set")}}</span>
          <code>${{formatFeatureValue(example.value)}}</code>
        </div>`).join("");
      return `<section class="example-section" data-band="${{escapeHtml(band || "")}}">
        <h3><span class="value-band-dot" aria-hidden="true"></span>${{escapeHtml(titleText)}}</h3>
        <p class="muted">${{escapeHtml(description)}}</p>
        <div class="example-strip">${{cards || '<span class="muted">No examples available.</span>'}}</div>
      </section>`;
    }}

    function correlationPartnerHtml(label, partner) {{
      if (!partner) {{
        return `<div class="correlation-item"><span>${{escapeHtml(label)}}</span><p class="muted">No partner available.</p></div>`;
      }}
      const isExplorerFeature = (dashboard.feature_explorer.features || [])
        .some(feature => feature.feature_id === partner.feature_id);
      const partnerControl = isExplorerFeature
        ? `<button type="button" data-explorer-partner="${{escapeHtml(partner.feature_id)}}">${{escapeHtml(partner.label)}}</button>`
        : `<b>${{escapeHtml(partner.label)}}</b>`;
      return `<div class="correlation-item">
        <span>${{escapeHtml(label)}}</span>
        ${{partnerControl}}
        <b>rho ${{formatSigned(partner.correlation)}} · ${{escapeHtml(bandLabel(partner.band))}}</b>
        <p class="muted">${{escapeHtml(partner.group_title || "Image feature")}} · N=${{escapeHtml(partner.pair_count)}}</p>
      </div>`;
    }}

    function openFeatureInExplorer(featureId) {{
      explorerState.group = "all";
      explorerState.search = "";
      explorerState.selectedFeatureId = featureId;
      document.getElementById("featureExplorerSearch").value = "";
      activateView("featureExplorer");
    }}

    function bandLabel(band) {{
      if (band === "high") return "High";
      if (band === "moderate") return "Moderate";
      return "Low";
    }}

    function render() {{
      if (state.variant === "image" && selectedFeatureIds().length === 0) {{
        renderNoFeatureSelection();
        return;
      }}
      const records = clusteringRecords();
      document.getElementById("datasetSummary").textContent = state.variant === "image"
        ? `${{records.length}} shared icons · ${{visibleFeatureSections().length}} feature families · ${{title(sharedSampleColorMode)}}`
        : `${{dashboard.metadata.row_count}} icons, ${{dashboard.metadata.per_set_sample_size}} random per dataset`;
      const projection = getProjection();
      const labels = projection.labels;
      const coords = projection.coords;
      const filtered = records.map((record, index) => ({{record, index}})).filter(item => passesFilters(item.record));
      const customData = filtered.map(item => [item.record.icon_id]);
      const plotPoints = filtered.map(item => [coords[item.index][0], coords[item.index][1]]);
      const ranges = plotRanges(plotPoints);

      Plotly.react("scatter", [{{
        x: filtered.map(item => coords[item.index][0]),
        y: filtered.map(item => coords[item.index][1]),
        mode: "markers",
        type: "scatter",
        marker: interactionMarker(),
        customdata: customData,
        hoverinfo: "none"
      }}], {{
        margin: {{l: 42, r: 14, t: 16, b: 42}},
        xaxis: {{title: "PCA 1", zeroline: false, range: ranges.x}},
        yaxis: {{title: "PCA 2", zeroline: false, range: ranges.y}},
        images: plotImages(filtered, coords, ranges),
        showlegend: false
      }}, {{responsive: true}});

      document.getElementById("scatter").on("plotly_click", event => {{
        selectedIconId = event.points[0].customdata[0];
        renderDetail(labels);
      }});
      document.getElementById("scatter").on("plotly_hover", event => {{
        const point = event.points[0];
        const iconId = point.customdata[0];
        const record = records.find(item => item.icon_id === iconId);
        if (record) renderHoverPreview(record, labels[records.indexOf(record)], event.event);
      }});
      document.getElementById("scatter").on("plotly_unhover", hideHoverPreview);
      renderDetail(labels);
      renderClusterSummary(labels, filtered);
    }}

    function renderNoFeatureSelection() {{
      hideHoverPreview();
      selectedIconId = null;
      Plotly.react("scatter", [], {{
        margin: {{l: 42, r: 14, t: 16, b: 42}},
        xaxis: {{title: "PCA 1", zeroline: false, visible: false}},
        yaxis: {{title: "PCA 2", zeroline: false, visible: false}},
        annotations: [{{
          text: "Select one or more image features to compute PCA and clustering.",
          xref: "paper",
          yref: "paper",
          x: 0.5,
          y: 0.5,
          showarrow: false,
          font: {{size: 16, color: "#5d6675"}}
        }}],
        showlegend: false
      }}, {{responsive: true}});
      document.getElementById("iconDetail").innerHTML =
        '<span class="muted">Select one or more image features, then click a point to inspect an icon.</span>';
      document.getElementById("clusterSummary").innerHTML =
        '<p class="muted">No feature-based clusters yet. Select features from the sidebar or use a preset.</p>';
    }}

    async function initializeAiClustering() {{
      document.getElementById("aiRunButton").addEventListener("click", runAiClustering);
      try {{
        const response = await fetch("/api/ai-clustering/status", {{cache: "no-store"}});
        if (!response.ok) throw new Error("Local AI service is unavailable.");
        aiState.service = await response.json();
        await refreshAiRuns();
      }} catch (error) {{
        aiState.service = {{configured: false, model_id: "Unavailable", message: "Start code/serve_analysis_dashboard.py to enable this experiment."}};
        aiState.error = error.message;
      }}
      renderAiClustering();
    }}

    function markAiClusteringStale() {{
      aiState.stale = true;
      if (reviewState.view === "aiClustering") renderAiClustering();
    }}

    function currentAiRecords() {{
      if (!sharedSampleFamilyId) return [];
      return combinedFamilySample(sharedSampleColorMode);
    }}

    function getImageProjection(records=currentAiRecords()) {{
      const features = selectedFeatureIds();
      if (!features.length || !records.length) return {{coords: [], labels: []}};
      const key = `image|${{state.method}}|${{state.k}}|${{features.join(",")}}|${{records.map(record => record.icon_id).join(",")}}`;
      if (computedCache.has(key)) return computedCache.get(key);
      const matrix = standardize(records.map(record => features.map(feature => Number(record.image_features[feature] || 0))));
      const effectiveK = Math.min(Number(state.k), records.length);
      const projection = {{
        coords: pca2d(matrix),
        labels: state.method === "hierarchical" ? hierarchicalLabels(matrix, effectiveK) : kmeansLabels(matrix, effectiveK)
      }};
      computedCache.set(key, projection);
      return projection;
    }}

    async function runAiClustering() {{
      const records = currentAiRecords();
      const projection = getImageProjection(records);
      if (!records.length || !selectedFeatureIds().length || !aiState.service?.configured) return;
      aiState.running = true;
      aiState.error = null;
      renderAiClustering();
      const payload = {{
        family_id: "all_families",
        cohort: sharedSampleColorMode,
        representative_feature_id: representativeFeatureIds().join(","),
        method: state.method,
        requested_k: Number(state.k),
        seed: 42,
        icon_ids: records.map(record => record.icon_id),
        feature_labels: projection.labels,
        feature_coords: projection.coords
      }};
      try {{
        const response = await fetch("/api/ai-clustering/runs", {{
          method: "POST", headers: {{"Content-Type": "application/json"}}, body: JSON.stringify(payload)
        }});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || `AI service returned ${{response.status}}`);
        aiState.currentRun = result;
        aiState.stale = false;
        if (aiState.service) {{
          aiState.service.cached_embeddings = Number(aiState.service.cached_embeddings || 0) + Number(result.cache_misses || 0);
          aiState.service.saved_runs = Number(aiState.service.saved_runs || 0) + 1;
        }}
        await refreshAiRuns();
      }} catch (error) {{
        aiState.error = error.message;
        try {{ await refreshAiRuns(); }} catch (_) {{ /* Preserve the original run error. */ }}
      }} finally {{
        aiState.running = false;
        renderAiClustering();
      }}
    }}

    async function refreshAiRuns() {{
      const response = await fetch("/api/ai-clustering/runs?limit=20", {{cache: "no-store"}});
      if (!response.ok) throw new Error("Recent AI runs could not be loaded.");
      aiState.recentRuns = (await response.json()).runs || [];
    }}

    async function loadAiRun(runId) {{
      try {{
        const response = await fetch(`/api/ai-clustering/runs/${{encodeURIComponent(runId)}}`, {{cache: "no-store"}});
        const run = await response.json();
        if (!response.ok) throw new Error(run.error || "Run could not be loaded.");
        aiState.currentRun = run;
        aiState.stale = true;
        aiState.error = null;
      }} catch (error) {{ aiState.error = error.message; }}
      renderAiClustering();
    }}

    function renderAiClustering() {{
      const container = document.getElementById("aiClusteringView");
      if (!container || !dashboard) return;
      const records = currentAiRecords();
      const service = aiState.service;
      const canRun = Boolean(service?.configured && records.length && selectedFeatureIds().length && !aiState.running);
      const runButton = document.getElementById("aiRunButton");
      runButton.disabled = !canRun;
      runButton.textContent = aiState.running ? "Running..." : "Run AI Clustering";
      let status = service?.message || "Checking the local AI service...";
      let kind = "ready";
      if (aiState.error) {{ status = aiState.error; kind = "error"; }}
      else if (aiState.running) status = "Requesting uncached image embeddings and computing the comparison...";
      else if (aiState.currentRun && aiState.stale) {{ status = "The displayed result is saved history or is stale because the sample or clustering settings changed. Run explicitly to refresh it."; kind = "stale"; }}
      else if (!selectedFeatureIds().length) {{ status = "Select at least one feature in Clustering before running this comparison."; kind = "stale"; }}
      document.getElementById("aiStatus").textContent = status;
      document.getElementById("aiStatus").dataset.kind = kind;
      document.getElementById("aiFacts").innerHTML = [
        ["Shared sample / cohort", `${{visibleFeatureSections().length}} families / ${{sharedSampleColorMode}}`],
        ["Icons", records.length],
        ["Model", service?.model_id || "—"],
        ["Method / k", `${{state.method}} / ${{state.k}}`],
        ["Stored cache", `${{service?.cached_embeddings ?? 0}} embeddings / ${{service?.saved_runs ?? 0}} runs`]
      ].map(([label, value]) => `<div class="ai-fact"><span>${{escapeHtml(label)}}</span><b>${{escapeHtml(value)}}</b></div>`).join("");
      if (aiState.currentRun?.status === "completed") renderAiRun(aiState.currentRun);
      else renderEmptyAiPlots(records);
      renderAiHistory();
    }}

    function renderEmptyAiPlots(records) {{
      const projection = getImageProjection(records);
      renderAiPlot("aiFeatureScatter", records.map((record, index) => ({{...record, x: projection.coords[index]?.[0] || 0, y: projection.coords[index]?.[1] || 0, cluster: projection.labels[index] || 0}})), "Feature cluster");
      Plotly.react("aiEmbeddingScatter", [], {{annotations: [{{text: "Run AI Clustering to compute image embeddings.", x: .5, y: .5, xref: "paper", yref: "paper", showarrow: false}}], xaxis: {{visible: false}}, yaxis: {{visible: false}}}}, {{responsive: true}});
      document.getElementById("aiMetrics").innerHTML = "";
      document.getElementById("aiCrossTable").innerHTML = '<p class="muted" style="padding:10px">No completed comparison loaded.</p>';
    }}

    function renderAiRun(run) {{
      const lookup = new Map([...(dashboard.feature_group_records || []), ...(dashboard.records || [])].map(record => [record.icon_id, record]));
      const featureItems = run.items.map(item => ({{...lookup.get(item.icon_id), x: item.feature_x, y: item.feature_y, cluster: item.feature_label}}));
      const aiItems = run.items.map(item => ({{...lookup.get(item.icon_id), x: item.ai_x, y: item.ai_y, cluster: item.ai_label}}));
      renderAiPlot("aiFeatureScatter", featureItems, "Feature cluster");
      renderAiPlot("aiEmbeddingScatter", aiItems, "AI cluster");
      synchronizeAiPlots();
      const metrics = run.metrics || {{}};
      document.getElementById("aiMetrics").innerHTML = [
        ["Pairwise agreement", metrics.pairwise_same_cluster_agreement],
        ["Cache", `${{run.cache_hits}} hit / ${{run.cache_misses}} miss`]
      ].map(([label, value]) => `<div class="ai-fact"><span>${{escapeHtml(label)}}</span><b>${{typeof value === "number" ? value.toFixed(3) : escapeHtml(value ?? "—")}}</b></div>`).join("");
      renderAiCrossTable(metrics.cross_table);
      if (run.warning && !aiState.error) {{ document.getElementById("aiStatus").textContent = run.warning; document.getElementById("aiStatus").dataset.kind = "stale"; }}
    }}

    function renderAiPlot(id, items, clusterTitle) {{
      const coords = items.map(item => [Number(item.x), Number(item.y)]);
      const ranges = plotRanges(coords);
      Plotly.react(id, [{{x: coords.map(point => point[0]), y: coords.map(point => point[1]), mode: "markers", marker: {{...interactionMarker(), color: items.map(item => item.cluster)}}, selected: {{marker: {{size: 38, opacity: .35, color: "#a000a8", line: {{width: 2, color: "#a000a8"}}}}}}, unselected: {{marker: {{opacity: .01}}}}, customdata: items.map(item => [item.icon_id]), hoverinfo: "none"}}], {{
        margin: {{l: 38, r: 12, t: 12, b: 38}}, xaxis: {{title: "PCA 1", range: ranges.x}}, yaxis: {{title: "PCA 2", range: ranges.y}},
        images: items.map(item => ({{source: item.normalized_path, xref: "x", yref: "y", x: item.x, y: item.y, sizex: ranges.spanX * .08, sizey: ranges.spanY * .08, xanchor: "center", yanchor: "middle", sizing: "contain", layer: "above"}})), showlegend: false
      }}, {{responsive: true}});
    }}

    function synchronizeAiPlots() {{
      let syncing = false;
      [["aiFeatureScatter", "aiEmbeddingScatter"], ["aiEmbeddingScatter", "aiFeatureScatter"]].forEach(([source, target]) => {{
        const plot = document.getElementById(source);
        plot.on("plotly_hover", event => {{ if (!syncing) {{ syncing = true; Plotly.Fx.hover(target, [{{curveNumber: 0, pointNumber: event.points[0].pointNumber}}]); syncing = false; }} }});
        plot.on("plotly_unhover", () => Plotly.Fx.unhover(target));
        plot.on("plotly_click", event => {{
          const selected = event.points[0].pointNumber;
          Plotly.restyle("aiFeatureScatter", {{selectedpoints: [[selected]]}});
          Plotly.restyle("aiEmbeddingScatter", {{selectedpoints: [[selected]]}});
        }});
      }});
    }}

    function renderAiCrossTable(table) {{
      if (!table) {{ document.getElementById("aiCrossTable").innerHTML = ""; return; }}
      document.getElementById("aiCrossTable").innerHTML = `<table class="ai-table"><thead><tr><th>Feature \\ AI</th>${{table.ai_labels.map(label => `<th>${{label}}</th>`).join("")}}</tr></thead><tbody>${{table.feature_labels.map((label, row) => `<tr><th>${{label}}</th>${{table.counts[row].map(count => `<td>${{count}}</td>`).join("")}}</tr>`).join("")}}</tbody></table>`;
    }}

    function renderAiHistory() {{
      const rows = aiState.recentRuns || [];
      document.getElementById("aiRecentRuns").innerHTML = rows.length ? `<table class="ai-table"><thead><tr><th>Time</th><th>Family</th><th>Status</th><th>Method</th><th></th></tr></thead><tbody>${{rows.map(run => `<tr><td>${{escapeHtml(new Date(run.created_at).toLocaleString())}}</td><td>${{escapeHtml(run.family_id)}} / ${{escapeHtml(run.cohort)}}</td><td>${{escapeHtml(run.status)}}</td><td>${{escapeHtml(run.method)}} k=${{run.effective_k}}</td><td>${{run.status === "completed" ? `<button type="button" data-ai-load="${{escapeHtml(run.run_id)}}">Load</button>` : escapeHtml(run.error || "—")}}</td></tr>`).join("")}}</tbody></table>` : '<p class="muted" style="padding:10px">No saved runs yet.</p>';
      document.querySelectorAll("[data-ai-load]").forEach(button => button.addEventListener("click", () => loadAiRun(button.dataset.aiLoad)));
    }}

    function getProjection() {{
      if (state.variant !== "image") {{
        return {{
          coords: dashboard.clusters[state.variant].pca,
          labels: dashboard.clusters[state.variant][state.method][state.k].labels
        }};
      }}
      return getImageProjection(clusteringRecords());
    }}

    function passesFilters(record) {{
      if (state.setFilter.size && !state.setFilter.has(record.set_name)) return false;
      return true;
    }}

    function clearSelectFilter(selectId, stateKey) {{
      Array.from(document.getElementById(selectId).options).forEach(option => option.selected = false);
      state[stateKey] = new Set();
      renderFilterPills();
      render();
    }}

    function resetFilters() {{
      clearSelectFilter("setFilter", "setFilter");
    }}

    function installToggleMultiSelect(selectId, stateKey) {{
      const select = document.getElementById(selectId);
      select.addEventListener("mousedown", event => {{
        if (event.target.tagName !== "OPTION") return;
        event.preventDefault();
        event.target.selected = !event.target.selected;
        state[stateKey] = new Set(Array.from(select.selectedOptions).map(option => option.value));
        renderFilterPills();
        render();
      }});
    }}

    function removeFilterValue(selectId, stateKey, value) {{
      const select = document.getElementById(selectId);
      Array.from(select.options).forEach(option => {{
        if (option.value === value) option.selected = false;
      }});
      state[stateKey].delete(value);
      renderFilterPills();
      render();
    }}

    function renderFilterPills() {{
      renderPillGroup("setFilterPills", "setFilter", "setFilter");
    }}

    function renderPillGroup(containerId, selectId, stateKey) {{
      const container = document.getElementById(containerId);
      const values = Array.from(state[stateKey]).sort();
      if (!values.length) {{
        container.innerHTML = '<span class="muted">All</span>';
        return;
      }}
      container.innerHTML = values.map(value => `
        <span class="filter-pill">
          <span>${{escapeHtml(value)}}</span>
          <button type="button" aria-label="Remove ${{escapeHtml(value)}}" data-value="${{escapeHtml(value)}}">x</button>
        </span>`).join("");
      container.querySelectorAll("button").forEach(button => {{
        button.addEventListener("click", () => removeFilterValue(selectId, stateKey, button.dataset.value));
      }});
    }}

    function interactionMarker() {{
      return {{
        size: 30,
        color: "rgba(24,32,47,0.01)",
        line: {{width: 0}},
        opacity: 0.01
      }};
    }}

    function plotRanges(points) {{
      if (!points.length) return {{x: [-1, 1], y: [-1, 1], spanX: 2, spanY: 2}};
      const xs = points.map(point => point[0]);
      const ys = points.map(point => point[1]);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const spanX = Math.max(maxX - minX, 1);
      const spanY = Math.max(maxY - minY, 1);
      const padX = spanX * 0.12;
      const padY = spanY * 0.12;
      return {{
        x: [minX - padX, maxX + padX],
        y: [minY - padY, maxY + padY],
        spanX,
        spanY
      }};
    }}

    function plotImages(filtered, coords, ranges) {{
      const sizeX = ranges.spanX * 0.055;
      const sizeY = ranges.spanY * 0.055;
      return filtered.map(item => ({{
        source: item.record.normalized_path,
        xref: "x",
        yref: "y",
        x: coords[item.index][0],
        y: coords[item.index][1],
        sizex: sizeX,
        sizey: sizeY,
        xanchor: "center",
        yanchor: "middle",
        sizing: "contain",
        layer: "above",
        opacity: 0.96
      }}));
    }}

    function renderHoverPreview(record, cluster, event) {{
      const preview = document.getElementById("hoverPreview");
      const features = groupedFeatureHtml(record, selectedFeatureIds(), false, 10);
      preview.innerHTML = `
        <div class="hover-grid">
          <img src="${{record.normalized_path}}" alt="">
          <div class="hover-meta">
            <b>${{escapeHtml(record.label)}}</b><br>
            ${{escapeHtml(record.set_name)}}<br>
            <b>Cluster: ${{cluster}}</b>
          </div>
        </div>
        <div class="hover-features">${{features}}</div>`;
      preview.style.display = "block";
      placeHoverPreview(event);
    }}

    function placeHoverPreview(event) {{
      const preview = document.getElementById("hoverPreview");
      if (!preview || !event) return;
      const margin = 8;
      const offset = 14;
      const width = preview.offsetWidth || 360;
      const height = preview.offsetHeight || 180;
      let left = event.clientX + offset;
      let top = event.clientY + offset;
      if (left + width + margin > window.innerWidth) left = event.clientX - width - offset;
      if (top + height + margin > window.innerHeight) top = event.clientY - height - offset;
      left = Math.min(Math.max(margin, left), Math.max(margin, window.innerWidth - width - margin));
      top = Math.min(Math.max(margin, top), Math.max(margin, window.innerHeight - height - margin));
      preview.style.left = `${{left}}px`;
      preview.style.top = `${{top}}px`;
    }}

    function hideHoverPreview() {{
      document.getElementById("hoverPreview").style.display = "none";
    }}

    function renderDetail(labels) {{
      const detail = document.getElementById("iconDetail");
      const records = clusteringRecords();
      const record = records.find(r => r.icon_id === selectedIconId);
      if (!record) {{
        detail.innerHTML = '<span class="muted">Click a point to inspect an icon from the shared sample.</span>';
        return;
      }}
      const index = records.indexOf(record);
      const featureGroups = groupedFeatureHtml(record, visibleFeatureIds(), true, null);
      const mcdougallRows = Object.entries(record.mcdougall || {{}})
        .filter(([, value]) => value !== "")
        .map(([key, value]) => `<span class="pill">${{title(key)}}: ${{escapeHtml(String(value))}}</span>`).join("");
      detail.innerHTML = `
        <img class="detail-img" src="${{record.normalized_path}}" alt="">
        <h3>${{escapeHtml(record.label)}}</h3>
        <p class="muted">${{escapeHtml(record.set_name)}}<br>Cluster: ${{labels[index]}}</p>
        ${{featureGroups}}
        <p>${{mcdougallRows}}</p>
        <p class="muted">${{escapeHtml(record.metadata_tokens || "").slice(0, 300)}}</p>`;
    }}

    function renderClusterSummary(labels, filtered) {{
      const container = document.getElementById("clusterSummary");
      const byCluster = new Map();
      filtered.forEach(item => {{
        const cluster = labels[item.index];
        if (!byCluster.has(cluster)) byCluster.set(cluster, []);
        byCluster.get(cluster).push(item);
      }});
      container.innerHTML = Array.from(byCluster.entries()).sort((a,b) => a[0]-b[0]).map(([cluster, items]) => {{
        const topSets = topCounts(items.map(item => item.record.set_name), 2).join(", ");
        const explanation = clusterExplanation(labels, cluster, selectedFeatureIds());
        const icons = items.slice(0, 12).map(item => `
          <div class="rep-icon">
            <img src="${{item.record.normalized_path}}" title="${{escapeHtml(item.record.label)}}" alt="">
            <span title="${{escapeHtml(item.record.label)}}">${{escapeHtml(item.record.label)}}</span>
          </div>`).join("");
        return `<details class="summary-cluster">
          <summary><b>${{methodLabel()}} cluster ${{cluster}}</b> <span class="muted">(${{items.length}} icons)</span><br>
            <span class="muted">Sets: ${{escapeHtml(topSets)}}</span></summary>
          <div class="summary-details">
            ${{explanation}}
            <div class="rep-icons">${{icons}}</div>
          </div>
        </details>`;
      }}).join("");
    }}

    function methodLabel() {{
      return state.method === "hierarchical" ? "Hierarchical" : "K-Means";
    }}

    function groupedFeatureHtml(record, featureIds, includeDescriptions=true, maxFeatures=null) {{
      const selected = new Set(featureIds);
      const featureLimit = maxFeatures === null ? featureIds.length : maxFeatures;
      let shown = 0;
      const html = visibleFeatureSections().map(section => {{
        const features = section.features.filter(feature => selected.has(feature.id));
        if (!features.length || shown >= featureLimit) return "";
        const visible = features.slice(0, Math.max(0, featureLimit - shown));
        shown += visible.length;
        const rows = visible.map(feature => `
          <tr>
            <td title="${{escapeHtml(feature.meaning)}}">${{escapeHtml(feature.label)}}</td>
            <td>${{formatFeatureValue(record.image_features[feature.id])}}</td>
          </tr>`).join("");
        const description = includeDescriptions ? `<p>${{escapeHtml(section.description)}}</p>` : "";
        const familyReading = includeDescriptions ? `
          <p class="family-reading"><b>Human perception:</b> ${{escapeHtml(section.perception || "This family describes a perceptual visual channel.")}}</p>
          <p class="family-reading"><b>Low:</b> ${{escapeHtml(section.low_value || "Lower values mean less of this family signal.")}}</p>
          <p class="family-reading"><b>High:</b> ${{escapeHtml(section.high_value || "Higher values mean more of this family signal.")}}</p>` : "";
        return `<div class="feature-group-detail">
          <h4>${{escapeHtml(section.title)}}</h4>
          ${{description}}
          ${{familyReading}}
          <table>${{rows}}</table>
        </div>`;
      }}).join("");
      const omitted = featureIds.length - shown;
      return html + (omitted > 0 ? `<p class="muted">${{omitted}} more selected features.</p>` : "");
    }}

    function featureSummaryLines(record, featureIds, maxFeatures) {{
      const selected = new Set(featureIds);
      const lines = [];
      for (const section of visibleFeatureSections()) {{
        for (const feature of section.features) {{
          if (!selected.has(feature.id)) continue;
          if (lines.length >= maxFeatures) {{
            lines.push(`${{featureIds.length - maxFeatures}} more selected features`);
            return lines;
          }}
          lines.push(`${{escapeHtml(feature.label)}}: ${{formatFeatureValue(record.image_features[feature.id])}}`);
        }}
      }}
      return lines;
    }}

    function clusterExplanation(labels, cluster, featureIds) {{
      if (!featureIds.length) return '<div class="summary-explain">No image features selected for cluster explanation.</div>';
      const features = featureIds;
      const matrix = standardizedImageMatrix(features);
      const members = labels.map((label, index) => label === cluster ? index : -1).filter(index => index >= 0);
      if (!members.length) return "";
      const featureIndex = new Map(features.map((feature, index) => [feature, index]));
      const sectionScores = visibleFeatureSections().map(section => {{
        const entries = section.features
          .filter(feature => featureIndex.has(feature.id))
          .map(feature => {{
            const column = featureIndex.get(feature.id);
            const mean = members.reduce((sum, index) => sum + matrix[index][column], 0) / members.length;
            return {{feature, score: Math.abs(mean)}};
          }});
        const score = entries.length ? entries.reduce((sum, entry) => sum + entry.score, 0) / entries.length : 0;
        return {{section, score, entries: entries.sort((a,b) => b.score - a.score)}};
      }}).filter(item => item.entries.length).sort((a,b) => b.score - a.score);
      const groups = sectionScores.slice(0, 2).map(item => `${{item.section.title.replace(" Features", "")}} (${{item.score.toFixed(2)}}z)`).join(", ");
      const topFeatures = sectionScores.flatMap(item => item.entries.slice(0, 3))
        .sort((a,b) => b.score - a.score)
        .slice(0, 3)
        .map(item => `${{item.feature.label}} (${{item.score.toFixed(2)}}z)`)
        .join(", ");
      return `<div class="summary-explain">Distinctive groups: ${{escapeHtml(groups)}}<br>Top features: ${{escapeHtml(topFeatures)}}</div>`;
    }}

    function standardizedImageMatrix(features) {{
      return standardize(clusteringRecords().map(record => features.map(feature => Number(record.image_features[feature] || 0))));
    }}

    function formatFeatureValue(value) {{
      if (typeof value === "number") {{
        const rounded = Math.round(value * 10000) / 10000;
        return escapeHtml(String(rounded));
      }}
      return escapeHtml(String(value ?? ""));
    }}

    function formatNumber(value) {{
      const number = Number(value);
      if (!Number.isFinite(number)) return "";
      return escapeHtml(number.toFixed(3));
    }}

    function formatSigned(value) {{
      const number = Number(value);
      if (!Number.isFinite(number)) return "";
      const formatted = `${{number >= 0 ? "+" : ""}}${{number.toFixed(3)}}`;
      return escapeHtml(formatted);
    }}

    function fillColorSelect(id, selected) {{
      const select = document.getElementById(id);
      select.innerHTML = "";
      appendOption(select, "cluster", "Cluster", selected);
      appendOption(select, "set_name", "Icon set", selected);
      clusteringFeatureSections().forEach(section => {{
        const group = document.createElement("optgroup");
        group.label = section.title;
        section.features.forEach(feature => appendOption(group, feature.id, feature.label, selected));
        select.appendChild(group);
      }});
    }}

    function appendOption(parent, value, label, selected) {{
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      option.selected = value === selected;
      parent.appendChild(option);
    }}

    function fillSelect(id, options, selected, multiple=false) {{
      const select = document.getElementById(id);
      select.innerHTML = "";
      select.multiple = multiple;
      options.forEach(([value, label]) => {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        option.selected = value === selected;
        select.appendChild(option);
      }});
    }}
    function unique(values) {{ return Array.from(new Set(values.filter(v => v !== undefined && v !== null && v !== ""))); }}
    function topCounts(values, limit) {{
      const counts = new Map();
      values.forEach(v => counts.set(v, (counts.get(v) || 0) + 1));
      return Array.from(counts.entries()).sort((a,b) => b[1]-a[1]).slice(0, limit).map(([v,n]) => `${{v}} (${{n}})`);
    }}
    function title(value) {{ return String(value).replaceAll("_", " ").replace(/\\b\\w/g, c => c.toUpperCase()); }}
    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#039;"}}[c]));
    }}
    function standardize(matrix) {{
      const rows = matrix.length;
      const cols = matrix[0].length;
      const means = Array(cols).fill(0);
      const stds = Array(cols).fill(0);
      matrix.forEach(row => row.forEach((value, col) => means[col] += value / rows));
      matrix.forEach(row => row.forEach((value, col) => stds[col] += Math.pow(value - means[col], 2) / rows));
      for (let col = 0; col < cols; col++) stds[col] = Math.sqrt(stds[col]) || 1;
      return matrix.map(row => row.map((value, col) => (value - means[col]) / stds[col]));
    }}
    function pca2d(matrix) {{
      const rows = matrix.length;
      const cols = matrix[0].length;
      if (cols === 1) return matrix.map(row => [row[0], 0]);
      const cov = Array.from({{length: cols}}, () => Array(cols).fill(0));
      for (const row of matrix) {{
        for (let i = 0; i < cols; i++) {{
          for (let j = i; j < cols; j++) cov[i][j] += row[i] * row[j] / Math.max(1, rows - 1);
        }}
      }}
      for (let i = 0; i < cols; i++) for (let j = 0; j < i; j++) cov[i][j] = cov[j][i];
      const eig = jacobiEigen(cov);
      const order = eig.values.map((value, index) => [value, index]).sort((a,b) => b[0] - a[0]).slice(0, 2).map(item => item[1]);
      return matrix.map(row => order.map(index => row.reduce((sum, value, col) => sum + value * eig.vectors[col][index], 0)));
    }}
    function jacobiEigen(input) {{
      const n = input.length;
      const a = input.map(row => row.slice());
      const v = Array.from({{length: n}}, (_, i) => Array.from({{length: n}}, (_, j) => i === j ? 1 : 0));
      for (let iter = 0; iter < 80; iter++) {{
        let p = 0, q = 1, max = 0;
        for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {{
          const value = Math.abs(a[i][j]);
          if (value > max) {{ max = value; p = i; q = j; }}
        }}
        if (max < 1e-10) break;
        const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
        const c = 1 / Math.sqrt(t * t + 1);
        const s = t * c;
        const app = a[p][p], aqq = a[q][q], apq = a[p][q];
        a[p][p] = app - t * apq;
        a[q][q] = aqq + t * apq;
        a[p][q] = 0; a[q][p] = 0;
        for (let r = 0; r < n; r++) if (r !== p && r !== q) {{
          const arp = a[r][p], arq = a[r][q];
          a[r][p] = a[p][r] = c * arp - s * arq;
          a[r][q] = a[q][r] = s * arp + c * arq;
        }}
        for (let r = 0; r < n; r++) {{
          const vrp = v[r][p], vrq = v[r][q];
          v[r][p] = c * vrp - s * vrq;
          v[r][q] = s * vrp + c * vrq;
        }}
      }}
      return {{values: a.map((row, i) => row[i]), vectors: v}};
    }}
    function kmeansLabels(matrix, k) {{
      const centers = matrix.slice(0, k).map(row => row.slice());
      let labels = Array(matrix.length).fill(0);
      for (let iter = 0; iter < 60; iter++) {{
        let changed = false;
        labels = matrix.map((row, rowIndex) => {{
          let best = 0, bestDistance = Infinity;
          centers.forEach((center, index) => {{
            const distance = squaredDistance(row, center);
            if (distance < bestDistance) {{ best = index; bestDistance = distance; }}
          }});
          if (best !== labels[rowIndex]) changed = true;
          return best;
        }});
        const sums = Array.from({{length: k}}, () => Array(matrix[0].length).fill(0));
        const counts = Array(k).fill(0);
        matrix.forEach((row, rowIndex) => {{
          counts[labels[rowIndex]]++;
          row.forEach((value, col) => sums[labels[rowIndex]][col] += value);
        }});
        for (let cluster = 0; cluster < k; cluster++) {{
          if (counts[cluster]) centers[cluster] = sums[cluster].map(value => value / counts[cluster]);
        }}
        if (!changed) break;
      }}
      return labels;
    }}
    function hierarchicalLabels(matrix, k) {{
      const edges = [];
      for (let i = 0; i < matrix.length; i++) {{
        for (let j = i + 1; j < matrix.length; j++) edges.push([Math.sqrt(squaredDistance(matrix[i], matrix[j])), i, j]);
      }}
      edges.sort((a,b) => a[0] - b[0]);
      const parent = Array.from({{length: matrix.length}}, (_, i) => i);
      const size = Array(matrix.length).fill(1);
      const mst = [];
      function find(x) {{ while (parent[x] !== x) {{ parent[x] = parent[parent[x]]; x = parent[x]; }} return x; }}
      for (const [, left, right] of edges) {{
        let a = find(left), b = find(right);
        if (a === b) continue;
        if (size[a] < size[b]) [a,b] = [b,a];
        parent[b] = a; size[a] += size[b]; mst.push([left, right]);
        if (mst.length === matrix.length - 1) break;
      }}
      return labelsFromMst(matrix.length, mst.slice(0, Math.max(0, matrix.length - k)));
    }}
    function labelsFromMst(count, edges) {{
      const parent = Array.from({{length: count}}, (_, i) => i);
      const size = Array(count).fill(1);
      function find(x) {{ while (parent[x] !== x) {{ parent[x] = parent[parent[x]]; x = parent[x]; }} return x; }}
      function union(left, right) {{
        let a = find(left), b = find(right);
        if (a === b) return;
        if (size[a] < size[b]) [a,b] = [b,a];
        parent[b] = a; size[a] += size[b];
      }}
      edges.forEach(([left, right]) => union(left, right));
      const map = new Map();
      return parent.map((_, index) => {{
        const root = find(index);
        if (!map.has(root)) map.set(root, map.size);
        return map.get(root);
      }});
    }}
    function squaredDistance(a, b) {{ return a.reduce((sum, value, index) => sum + Math.pow(value - b[index], 2), 0); }}
  </script>
</body>
</html>
"""
    (OUTPUT_DIR / "index.html").write_text(index, encoding="utf-8")


def write_metadata_report(rows: list[dict], failures: list[dict] | None = None) -> None:
    report = {
        "rows": len(rows),
        "per_set_sample_size": PER_SET_SAMPLE_SIZE,
        "random_seed": RANDOM_SEED,
        "set_counts": dict(sorted(Counter(row["set_id"] for row in rows).items())),
        "missing_metadata_tokens": sum(1 for row in rows if not row.get("metadata_tokens")),
        "missing_normalized_paths": sum(1 for row in rows if row.get("normalized_path_exists") != "true"),
        "expected_outputs": [
            "sample_metadata.csv",
            "features_image.csv",
            "features_metadata.csv",
            "features_combined.csv",
            "clusters_kmeans.csv",
            "clusters_hierarchical.csv",
            "cluster_summary.csv",
            "dashboard_data.json",
            "index.html",
        ],
    }
    (OUTPUT_DIR / "analysis_dashboard_metadata_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_plotly_placeholder_if_missing() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if PLOTLY_ASSET.exists():
        return
    PLOTLY_ASSET.write_text(
        "throw new Error('Missing Plotly asset. Replace assets/plotly.min.js with a local Plotly.js bundle.');\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = read_csv(DATASET_PATH)
    sampled_source_rows = sample_random_rows_per_set(all_rows, PER_SET_SAMPLE_SIZE, RANDOM_SEED)
    metadata_rows = enrich_metadata_rows(sampled_source_rows)
    write_rows(OUTPUT_DIR / "sample_metadata.csv", metadata_rows)
    write_metadata_report(metadata_rows)

    feature_rows = extract_features(sampled_source_rows)
    feature_by_id = {row["icon_id"]: row for row in feature_rows}
    metadata_rows = [row for row in metadata_rows if row["icon_id"] in feature_by_id]

    matrices = feature_matrices(metadata_rows, feature_by_id)
    write_feature_tables(metadata_rows, feature_by_id, matrices)

    clusters, assignment_rows, summary_rows = build_clusters(metadata_rows, matrices)
    write_rows(OUTPUT_DIR / "cluster_assignments.csv", assignment_rows)
    write_rows(OUTPUT_DIR / "clusters_kmeans.csv", [row for row in assignment_rows if row["method"] == "kmeans"])
    write_rows(
        OUTPUT_DIR / "clusters_hierarchical.csv",
        [row for row in assignment_rows if row["method"] == "hierarchical"],
    )
    write_rows(OUTPUT_DIR / "cluster_summary.csv", summary_rows)
    write_dashboard_data(metadata_rows, feature_by_id, matrices, clusters)
    write_index_html()
    write_plotly_placeholder_if_missing()
    print(f"Wrote analysis dashboard outputs to {OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
