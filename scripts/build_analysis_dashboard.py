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


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "icon_data" / "analysis"
DATASET_PATH = ANALYSIS_DIR / "dataset.csv"
OUTPUT_DIR = ANALYSIS_DIR / "analysis_dashboard"
ASSETS_DIR = OUTPUT_DIR / "assets"
PLOTLY_ASSET = ASSETS_DIR / "plotly.min.js"

PER_SET_LIMIT = 100
K_VALUES = (3, 5, 7, 10)
PRIMARY_K = 7
RANDOM_SEED = 42

METADATA_COLUMNS = [
    "icon_id",
    "set_id",
    "set_name",
    "icon_name",
    "label",
    "category",
    "original_category",
    "category_source",
    "style_label",
    "source",
    "source_url",
    "format",
    "filename",
    "relative_path",
    "normalized_path",
    "notes",
    "metadata_text",
    "metadata_tokens",
    "has_category",
    "has_notes",
    "source_path_exists",
    "normalized_path_exists",
]

IMAGE_FEATURE_COLUMNS = [
    "foreground_area_ratio",
    "canny_edge_density",
    "connected_components",
    "quadtree_leaf_count",
    "quadtree_structural_variability",
    "quadtree_mean_leaf_size",
]

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sample_per_set(rows: list[dict[str, str]], per_set_limit: int) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    sampled = []
    for row in rows:
        set_id = row["set_id"]
        count = counts.get(set_id, 0)
        if count >= per_set_limit:
            continue
        sampled.append(row)
        counts[set_id] = count + 1
    return sampled


def enrich_metadata_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ratings = metadata_helpers.load_mcdougall_ratings()
    enriched = []
    for source in rows:
        row = source.copy()
        set_id = row["set_id"]
        label = row.get("label", "")
        notes = row.get("notes", "")
        category = row.get("category", "")
        original_category = category
        category_source = "dataset.csv" if category else ""
        rating = None

        if set_id == "01_mcdougall_symbol_icon_set":
            appendix_item = metadata_helpers.notes_value(notes, "appendix_item")
            rating = ratings.get(appendix_item)
            if not category:
                category = metadata_helpers.infer_mcdougall_category(label, rating)
                category_source = "inferred_from_mcdougall_label_and_ratings"
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

        if set_id == "02_aiga_dot_symbol_signs" and not category:
            category = metadata_helpers.infer_aiga_category(label)
            category_source = "inferred_from_aiga_label"

        metadata_text = " | ".join(
            value for value in [label, category, row.get("set_name", ""), notes] if value
        )
        enriched.append(
            {
                "icon_id": row["icon_id"],
                "set_id": set_id,
                "set_name": row["set_name"],
                "icon_name": label,
                "label": label,
                "category": category,
                "original_category": original_category,
                "category_source": category_source,
                "style_label": metadata_helpers.infer_style_label(row),
                "source": row.get("source", ""),
                "source_url": row.get("source_url", ""),
                "format": row.get("format", ""),
                "filename": row.get("filename", ""),
                "relative_path": row.get("relative_path", ""),
                "normalized_path": row.get("normalized_path", ""),
                "notes": notes,
                "metadata_text": metadata_text,
                "metadata_tokens": metadata_helpers.text_tokens(label, category, row.get("set_name", ""), notes),
                "mcdougall_concreteness": (rating or {}).get("concreteness", ""),
                "mcdougall_complexity": (rating or {}).get("complexity", ""),
                "mcdougall_familiarity": (rating or {}).get("familiarity", ""),
                "mcdougall_meaningfulness": (rating or {}).get("meaningfulness", ""),
                "mcdougall_semantic_distance": (rating or {}).get("semantic_distance", ""),
                "mcdougall_concept_agreement": (rating or {}).get("concept_agreement", ""),
                "mcdougall_name_agreement": (rating or {}).get("name_agreement", ""),
                "mcdougall_common_response": (rating or {}).get("common_response", ""),
                "has_category": str(bool(category)).lower(),
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


def standardize(matrix: np.ndarray) -> tuple[np.ndarray, list[float], list[float]]:
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds = np.where(stds == 0, 1.0, stds)
    return (matrix - means) / stds, means.tolist(), stds.tolist()


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
    image = np.array(
        [[to_float(feature_by_id[row["icon_id"]].get(column)) for column in IMAGE_FEATURE_COLUMNS] for row in rows],
        dtype=float,
    )
    image_scaled, image_means, image_stds = standardize(image)

    set_matrix, set_columns = one_hot(rows, "set_name", "set")
    category_matrix, category_columns = one_hot(rows, "category", "category", max_values=60)
    style_matrix, style_columns = one_hot(rows, "style_label", "style")
    token_matrix, token_columns = token_features(rows)
    mcdougall = np.array(
        [[to_float(row.get(column)) for column in MCDOUGALL_NUMERIC_COLUMNS] for row in rows],
        dtype=float,
    )
    mcdougall_scaled, _, _ = standardize(mcdougall)

    metadata_matrix = np.hstack([set_matrix, category_matrix, style_matrix, token_matrix, mcdougall_scaled])
    metadata_columns = set_columns + category_columns + style_columns + token_columns + MCDOUGALL_NUMERIC_COLUMNS
    combined_matrix = np.hstack([image_scaled, metadata_matrix])

    return {
        "image": {
            "matrix": image_scaled,
            "columns": IMAGE_FEATURE_COLUMNS,
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
            "columns": IMAGE_FEATURE_COLUMNS + metadata_columns,
        },
    }


def pca_2d(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0)
    if centered.shape[1] == 1:
        return np.column_stack([centered[:, 0], np.zeros(len(centered))])
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[:2].T
    coords = centered @ components
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(len(coords))])
    return coords[:, :2]


def kmeans(matrix: np.ndarray, k: int, seed: int, iterations: int = 80) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed + k)
    if k >= len(matrix):
        labels = np.arange(len(matrix), dtype=int)
        return labels, matrix.copy()
    centers = matrix[rng.choice(len(matrix), size=k, replace=False)].copy()
    labels = np.zeros(len(matrix), dtype=int)
    for _ in range(iterations):
        distances = squared_distances(matrix, centers)
        new_labels = distances.argmin(axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for cluster in range(k):
            members = matrix[labels == cluster]
            if len(members):
                centers[cluster] = members.mean(axis=0)
            else:
                centers[cluster] = matrix[rng.integers(0, len(matrix))]
    return labels, centers


def squared_distances(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)


def silhouette_proxy(matrix: np.ndarray, labels: np.ndarray, centers: np.ndarray) -> float:
    own = np.linalg.norm(matrix - centers[labels], axis=1)
    distances = np.linalg.norm(matrix[:, None, :] - centers[None, :, :], axis=2)
    if centers.shape[0] > 1:
        distances[np.arange(len(matrix)), labels] = np.inf
        nearest_other = distances.min(axis=1)
    else:
        nearest_other = np.zeros(len(matrix))
    denom = np.maximum(own, nearest_other)
    scores = np.where(denom > 0, (nearest_other - own) / denom, 0.0)
    return float(scores.mean())


def pairwise_distances(matrix: np.ndarray) -> np.ndarray:
    norms = (matrix**2).sum(axis=1)
    squared = norms[:, None] + norms[None, :] - 2 * matrix @ matrix.T
    squared = np.maximum(squared, 0.0)
    return np.sqrt(squared)


def hierarchical_single_linkage_labels(matrix: np.ndarray, k_values: tuple[int, ...]) -> dict[int, np.ndarray]:
    distances = pairwise_distances(matrix)
    edges = []
    for i in range(len(matrix)):
        row = distances[i, i + 1 :]
        for offset, distance in enumerate(row, start=i + 1):
            edges.append((float(distance), i, offset))
    edges.sort(key=lambda item: item[0])

    parent = list(range(len(matrix)))
    size = [1] * len(matrix)
    mst_edges = []

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for distance, left, right in edges:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            continue
        if size[root_left] < size[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        size[root_left] += size[root_right]
        mst_edges.append((distance, left, right))
        if len(mst_edges) == len(matrix) - 1:
            break

    labels_by_k = {}
    for k in k_values:
        labels_by_k[k] = labels_from_mst(len(matrix), mst_edges, k)
    return labels_by_k


def labels_from_mst(node_count: int, mst_edges: list[tuple[float, int, int]], k: int) -> np.ndarray:
    kept_edges = sorted(mst_edges, key=lambda item: item[0])[: max(0, node_count - k)]
    parent = list(range(node_count))
    size = [1] * node_count

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return
        if size[root_left] < size[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        size[root_left] += size[root_right]

    for _, left, right in kept_edges:
        union(left, right)

    cluster_index: dict[int, int] = {}
    labels = np.zeros(node_count, dtype=int)
    for item in range(node_count):
        root = find(item)
        if root not in cluster_index:
            cluster_index[root] = len(cluster_index)
        labels[item] = cluster_index[root]
    return labels


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
        category_counts = Counter(row["category"] for row in subset).most_common(5)
        summaries.append(
            {
                "method": method,
                "variant": variant,
                "k": k,
                "cluster": int(cluster),
                "size": len(indices),
                "top_sets": json.dumps(set_counts, ensure_ascii=False),
                "top_categories": json.dumps(category_counts, ensure_ascii=False),
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
                "category": row.get("category", ""),
                "style_label": row.get("style_label", ""),
                "format": row.get("format", ""),
                "normalized_path": relative_to_dashboard(ROOT / row.get("normalized_path", "")),
                "metadata_tokens": row.get("metadata_tokens", ""),
                "image_features": image_features,
                "mcdougall": mcdougall,
            }
        )

    data = {
        "metadata": {
            "generated_from": str(DATASET_PATH.relative_to(ROOT)),
            "row_count": len(records),
            "per_set_limit": PER_SET_LIMIT,
            "k_values": list(K_VALUES),
            "primary_k": PRIMARY_K,
            "feature_variants": list(FEATURE_VARIANTS),
            "image_feature_columns": IMAGE_FEATURE_COLUMNS,
            "mcdougall_numeric_columns": MCDOUGALL_NUMERIC_COLUMNS,
        },
        "records": records,
        "feature_columns": {variant: matrices[variant]["columns"] for variant in FEATURE_VARIANTS},
        "clusters": clusters,
    }
    (OUTPUT_DIR / "dashboard_data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def relative_to_dashboard(path: Path) -> str:
    return os.path.relpath(path, OUTPUT_DIR)


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
    header {{ padding: 14px 18px; border-bottom: 1px solid var(--border); display: flex; align-items: baseline; gap: 18px; }}
    h1 {{ font-size: 18px; margin: 0; font-weight: 650; }}
    header span {{ color: var(--muted); font-size: 13px; }}
    main {{ display: grid; grid-template-columns: 300px minmax(520px, 1fr) 330px; min-height: calc(100vh - 52px); }}
    aside {{ border-right: 1px solid var(--border); padding: 14px; overflow: auto; max-height: calc(100vh - 52px); }}
    aside.right {{ border-left: 1px solid var(--border); border-right: 0; }}
    section.control {{ margin-bottom: 18px; }}
    h2 {{ font-size: 13px; margin: 0 0 8px; text-transform: uppercase; color: #3d4656; letter-spacing: .04em; }}
    label {{ display: block; font-size: 13px; margin: 7px 0; }}
    select, input[type="range"] {{ width: 100%; }}
    select {{ min-height: 30px; border: 1px solid var(--border); border-radius: 6px; background: white; padding: 4px 6px; }}
    button {{ border: 1px solid var(--border); border-radius: 6px; background: white; padding: 6px 9px; color: #18202f; cursor: pointer; }}
    button:hover {{ background: var(--panel); }}
    .button-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
    .selected-pills {{ display: flex; gap: 5px; flex-wrap: wrap; margin: 6px 0 10px; min-height: 20px; }}
    .filter-pill {{ display: inline-flex; align-items: center; gap: 5px; max-width: 100%; padding: 3px 7px; border: 1px solid #cbd2de; border-radius: 999px; background: #eef2f7; font-size: 12px; color: #18202f; }}
    .filter-pill button {{ border: 0; background: transparent; padding: 0; width: 16px; height: 16px; line-height: 14px; font-size: 14px; color: #4d5665; }}
    .filter-pill button:hover {{ background: #dde3ec; border-radius: 999px; }}
    .checklist {{ border: 1px solid var(--border); border-radius: 6px; padding: 6px 8px; max-height: 180px; overflow: auto; background: white; }}
    .plot-wrap {{ padding: 10px; min-width: 0; }}
    #scatter {{ width: 100%; height: calc(100vh - 76px); }}
    #hoverPreview {{ position: fixed; z-index: 20; display: none; pointer-events: none; max-width: 260px; padding: 8px; border: 1px solid var(--border); border-radius: 8px; background: rgba(255,255,255,.98); box-shadow: 0 8px 24px rgba(20,30,45,.16); font-size: 12px; }}
    #hoverPreview img {{ width: 72px; height: 72px; object-fit: contain; border: 1px solid var(--border); background: white; float: left; margin-right: 8px; }}
    #hoverPreview b {{ font-size: 13px; }}
    .detail-img {{ width: 96px; height: 96px; object-fit: contain; border: 1px solid var(--border); background: white; }}
    .muted {{ color: var(--muted); }}
    .pill {{ display: inline-block; padding: 2px 6px; border: 1px solid var(--border); border-radius: 999px; margin: 2px; font-size: 12px; background: var(--panel); }}
    .summary-cluster {{ border: 1px solid var(--border); border-radius: 8px; padding: 8px; margin: 8px 0; background: white; }}
    .rep-icons {{ display: flex; gap: 4px; flex-wrap: wrap; margin-top: 6px; }}
    .rep-icons img {{ width: 34px; height: 34px; object-fit: contain; border: 1px solid var(--border); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    td {{ border-bottom: 1px solid #edf0f4; padding: 4px 0; vertical-align: top; }}
    td:last-child {{ text-align: right; color: #334; }}
  </style>
</head>
<body>
  <header>
    <h1>Analysis Icon Clustering Dashboard</h1>
    <span id="datasetSummary">Loading data...</span>
  </header>
  <main>
    <aside>
      <section class="control">
        <h2>Feature Variant</h2>
        <label><select id="variantSelect"></select></label>
      </section>
      <section class="control">
        <h2>Clustering</h2>
        <div hidden>
          <label>Method<select id="methodSelect"><option value="kmeans">K-Means</option><option value="hierarchical">Hierarchical</option></select></label>
        </div>
        <label>Cluster count<select id="kSelect"></select></label>
        <label>Color by<select id="colorSelect"></select></label>
      </section>
      <section class="control">
        <h2>Image Features</h2>
        <div class="checklist" id="featureChecks"></div>
      </section>
      <section class="control">
        <h2>Filters</h2>
        <label>Icon sets<select id="setFilter" multiple size="8"></select></label>
        <div class="selected-pills" id="setFilterPills"></div>
        <div hidden>
          <label>Categories<select id="categoryFilter" multiple size="8"></select></label>
          <div class="selected-pills" id="categoryFilterPills"></div>
          <label>Styles<select id="styleFilter" multiple size="5"></select></label>
          <div class="selected-pills" id="styleFilterPills"></div>
        </div>
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
  <div id="hoverPreview"></div>
  <script>
    let dashboard = null;
    let selectedIconId = null;
    const computedCache = new Map();

    const state = {{
      variant: "image",
      method: "kmeans",
      k: "{PRIMARY_K}",
      color: "cluster",
      activeFeatures: new Set(),
      setFilter: new Set(),
      categoryFilter: new Set(),
      styleFilter: new Set()
    }};

    fetch("dashboard_data.json").then(r => r.json()).then(data => {{
      dashboard = data;
      initializeControls();
      render();
    }});

    function initializeControls() {{
      document.getElementById("datasetSummary").textContent =
        `${{dashboard.metadata.row_count}} icons, ${{dashboard.metadata.per_set_limit}} max per set`;

      fillSelect("variantSelect", dashboard.metadata.feature_variants.map(v => [v, title(v)]), state.variant);
      fillSelect("kSelect", dashboard.metadata.k_values.map(k => [String(k), String(k)]), state.k);
      fillSelect("colorSelect", [
        ["cluster", "Cluster"],
        ["set_name", "Icon set"],
        ["category", "Category"],
        ["style_label", "Style"],
        ...dashboard.metadata.image_feature_columns.map(f => [f, title(f)])
      ], state.color);

      state.activeFeatures = new Set(dashboard.metadata.image_feature_columns);
      const featureChecks = document.getElementById("featureChecks");
      dashboard.metadata.image_feature_columns.forEach(feature => {{
        const label = document.createElement("label");
        label.innerHTML = `<input type="checkbox" value="${{feature}}" checked> ${{title(feature)}}`;
        featureChecks.appendChild(label);
      }});

      const sets = unique(dashboard.records.map(r => r.set_name)).sort();
      const categories = unique(dashboard.records.map(r => r.category)).sort();
      const styles = unique(dashboard.records.map(r => r.style_label)).sort();
      fillSelect("setFilter", sets.map(v => [v, v]), "", true);
      fillSelect("categoryFilter", categories.map(v => [v, v]), "", true);
      fillSelect("styleFilter", styles.map(v => [v, v]), "", true);
      installToggleMultiSelect("setFilter", "setFilter");
      installToggleMultiSelect("categoryFilter", "categoryFilter");
      installToggleMultiSelect("styleFilter", "styleFilter");

      document.getElementById("variantSelect").addEventListener("change", e => {{ state.variant = e.target.value; render(); }});
      document.getElementById("methodSelect").addEventListener("change", e => {{ state.method = e.target.value; render(); }});
      document.getElementById("kSelect").addEventListener("change", e => {{ state.k = e.target.value; render(); }});
      document.getElementById("colorSelect").addEventListener("change", e => {{ state.color = e.target.value; render(); }});
      document.getElementById("setFilter").addEventListener("change", e => {{
        state.setFilter = new Set(Array.from(e.target.selectedOptions).map(o => o.value));
        renderFilterPills();
        render();
      }});
      document.getElementById("categoryFilter").addEventListener("change", e => {{
        state.categoryFilter = new Set(Array.from(e.target.selectedOptions).map(o => o.value));
        renderFilterPills();
        render();
      }});
      document.getElementById("styleFilter").addEventListener("change", e => {{
        state.styleFilter = new Set(Array.from(e.target.selectedOptions).map(o => o.value));
        renderFilterPills();
        render();
      }});
      document.getElementById("clearSetFilter").addEventListener("click", () => clearSelectFilter("setFilter", "setFilter"));
      document.getElementById("clearCategoryFilter").addEventListener("click", () => clearSelectFilter("categoryFilter", "categoryFilter"));
      document.getElementById("clearStyleFilter").addEventListener("click", () => clearSelectFilter("styleFilter", "styleFilter"));
      document.getElementById("resetFilters").addEventListener("click", resetFilters);
      featureChecks.addEventListener("change", () => {{
        state.activeFeatures = new Set(Array.from(featureChecks.querySelectorAll("input:checked")).map(i => i.value));
        render();
      }});
      renderFilterPills();
    }}

    function render() {{
      const projection = getProjection();
      const labels = projection.labels;
      const coords = projection.coords;
      const filtered = dashboard.records.map((record, index) => ({{record, index}})).filter(item => passesFilters(item.record));
      const colorValues = filtered.map(item => colorValue(item.record, labels[item.index]));
      const marker = markerFor(colorValues, state.color);
      const customData = filtered.map(item => [item.record.icon_id]);

      Plotly.react("scatter", [{{
        x: filtered.map(item => coords[item.index][0]),
        y: filtered.map(item => coords[item.index][1]),
        mode: "markers",
        type: "scattergl",
        marker,
        customdata: customData,
        text: filtered.map(item => hoverText(item.record, labels[item.index])),
        hovertemplate: "%{{text}}<extra></extra>"
      }}], {{
        margin: {{l: 42, r: 14, t: 16, b: 42}},
        xaxis: {{title: "PCA 1", zeroline: false}},
        yaxis: {{title: "PCA 2", zeroline: false}},
        showlegend: false
      }}, {{responsive: true}});

      document.getElementById("scatter").on("plotly_click", event => {{
        selectedIconId = event.points[0].customdata[0];
        renderDetail(labels);
      }});
      document.getElementById("scatter").on("plotly_hover", event => {{
        const point = event.points[0];
        const iconId = point.customdata[0];
        const record = dashboard.records.find(item => item.icon_id === iconId);
        if (record) renderHoverPreview(record, labels[dashboard.records.indexOf(record)], event.event);
      }});
      document.getElementById("scatter").on("plotly_unhover", hideHoverPreview);
      renderDetail(labels);
      renderClusterSummary(labels, filtered);
    }}

    function getProjection() {{
      if (state.variant !== "image") {{
        return {{
          coords: dashboard.clusters[state.variant].pca,
          labels: dashboard.clusters[state.variant][state.method][state.k].labels
        }};
      }}
      const features = Array.from(state.activeFeatures);
      if (!features.length) features.push(dashboard.metadata.image_feature_columns[0]);
      const key = `${{state.method}}|${{state.k}}|${{features.join(",")}}`;
      if (computedCache.has(key)) return computedCache.get(key);
      const matrix = standardize(dashboard.records.map(record => features.map(feature => Number(record.image_features[feature] || 0))));
      const coords = pca2d(matrix);
      const labels = state.method === "hierarchical" ? hierarchicalLabels(matrix, Number(state.k)) : kmeansLabels(matrix, Number(state.k));
      const projection = {{coords, labels}};
      computedCache.set(key, projection);
      return projection;
    }}

    function passesFilters(record) {{
      if (state.setFilter.size && !state.setFilter.has(record.set_name)) return false;
      if (state.categoryFilter.size && !state.categoryFilter.has(record.category)) return false;
      if (state.styleFilter.size && !state.styleFilter.has(record.style_label)) return false;
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
      clearSelectFilter("categoryFilter", "categoryFilter");
      clearSelectFilter("styleFilter", "styleFilter");
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
      renderPillGroup("categoryFilterPills", "categoryFilter", "categoryFilter");
      renderPillGroup("styleFilterPills", "styleFilter", "styleFilter");
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

    function colorValue(record, cluster) {{
      if (state.color === "cluster") return `Cluster ${{cluster}}`;
      if (record.image_features && state.color in record.image_features) return record.image_features[state.color];
      return record[state.color] || "";
    }}

    function markerFor(values, mode) {{
      if (dashboard.metadata.image_feature_columns.includes(mode)) {{
        return {{size: 8, color: values, colorscale: "Viridis", showscale: true, opacity: 0.78}};
      }}
      const categories = unique(values);
      const palette = ["#3366cc","#dc3912","#ff9900","#109618","#990099","#0099c6","#dd4477","#66aa00","#b82e2e","#316395","#994499","#22aa99","#aaaa11","#6633cc"];
      const map = new Map(categories.map((value, index) => [value, palette[index % palette.length]]));
      return {{size: 8, color: values.map(value => map.get(value)), opacity: 0.78}};
    }}

    function hoverText(record, cluster) {{
      const features = Array.from(state.activeFeatures).map(f => `${{title(f)}}: ${{record.image_features[f]}}`).join("<br>");
      return `<b>${{escapeHtml(record.label)}}</b><br>${{escapeHtml(record.set_name)}}<br>${{escapeHtml(record.category)}}<br>Cluster: ${{cluster}}<br>${{features}}`;
    }}

    function renderHoverPreview(record, cluster, event) {{
      const preview = document.getElementById("hoverPreview");
      preview.innerHTML = `
        <img src="${{record.normalized_path}}" alt="">
        <b>${{escapeHtml(record.label)}}</b><br>
        <span class="muted">${{escapeHtml(record.set_name)}}</span><br>
        <span>${{escapeHtml(record.category || "Uncategorized")}}</span><br>
        <span>Cluster: ${{cluster}}</span>
        <div style="clear: both;"></div>`;
      const x = Math.min(event.clientX + 14, window.innerWidth - 280);
      const y = Math.min(event.clientY + 14, window.innerHeight - 150);
      preview.style.left = `${{Math.max(8, x)}}px`;
      preview.style.top = `${{Math.max(8, y)}}px`;
      preview.style.display = "block";
    }}

    function hideHoverPreview() {{
      document.getElementById("hoverPreview").style.display = "none";
    }}

    function renderDetail(labels) {{
      const detail = document.getElementById("iconDetail");
      const record = dashboard.records.find(r => r.icon_id === selectedIconId);
      if (!record) return;
      const index = dashboard.records.indexOf(record);
      const featureRows = Object.entries(record.image_features)
        .filter(([key]) => state.activeFeatures.has(key))
        .map(([key, value]) => `<tr><td>${{title(key)}}</td><td>${{value}}</td></tr>`).join("");
      const mcdougallRows = Object.entries(record.mcdougall || {{}})
        .filter(([, value]) => value !== "")
        .map(([key, value]) => `<span class="pill">${{title(key)}}: ${{escapeHtml(String(value))}}</span>`).join("");
      detail.innerHTML = `
        <img class="detail-img" src="${{record.normalized_path}}" alt="">
        <h3>${{escapeHtml(record.label)}}</h3>
        <p class="muted">${{escapeHtml(record.set_name)}}<br>${{escapeHtml(record.category)}}<br>${{escapeHtml(record.style_label)}}<br>Cluster: ${{labels[index]}}</p>
        <table>${{featureRows}}</table>
        <p>${{mcdougallRows}}</p>
        <p class="muted">${{escapeHtml(record.metadata_tokens).slice(0, 300)}}</p>`;
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
        const topCats = topCounts(items.map(item => item.record.category), 2).join(", ");
        const icons = items.slice(0, 8).map(item => `<img src="${{item.record.normalized_path}}" title="${{escapeHtml(item.record.label)}}">`).join("");
        return `<div class="summary-cluster"><b>Cluster ${{cluster}}</b> <span class="muted">(${{items.length}} icons)</span><br>
          <span class="muted">Sets: ${{escapeHtml(topSets)}}<br>Categories: ${{escapeHtml(topCats)}}</span>
          <div class="rep-icons">${{icons}}</div></div>`;
      }}).join("");
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
        "per_set_limit": PER_SET_LIMIT,
        "set_counts": dict(sorted(Counter(row["set_id"] for row in rows).items())),
        "missing_category": sum(1 for row in rows if not row.get("category")),
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
    sampled_source_rows = sample_per_set(all_rows, PER_SET_LIMIT)
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
