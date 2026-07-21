#!/usr/bin/env python3
"""Compute pairwise feature similarity and nearest-neighbor visual checks."""

import argparse
import csv
import html
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

import build_analysis_dashboard
import extract_icon_features


ROOT = Path(__file__).resolve().parents[1]
FEATURES_CSV = ROOT / "icon_data/analysis/features.csv"
OUTPUT_DIR = ROOT / "icon_data/analysis/similarity"

FEATURE_COLUMNS = list(extract_icon_features.FEATURE_COLUMNS)
HUE_COLUMNS = [f"hue_histogram_{index:02d}" for index in range(12)]
ORIENTATION_COLUMN = "principal_axis_orientation_v2"
ORIENTATION_CONFIDENCE_COLUMN = "orientation_confidence_v2"
ORIENTATION_DERIVED_COLUMNS = [
    "principal_axis_orientation_v2_cos2",
    "principal_axis_orientation_v2_sin2",
]
BINARY_FEATURE_COLUMNS = {"is_monochrome"}
BOUNDED_VECTOR_FEATURE_COLUMNS = set(ORIENTATION_DERIVED_COLUMNS)
ROBUST_CLIP_Z = 5.0

FAMILY_RELIABILITY_WEIGHTS = {
    "Texture": 0.75,
}

FEATURE_CONFIDENCE_WEIGHTS = {
}

METADATA_COLUMNS = [
    "icon_id",
    "set_id",
    "set_name",
    "label",
    "category",
    "normalized_path",
]


def load_features(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in FEATURE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in METADATA_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].fillna("")
    return frame.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)


def compute_distances(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    similarity_frame = transformed_similarity_features(frame)
    similarity_columns = active_similarity_feature_columns()
    similarity_frame = similarity_frame[similarity_columns]
    scaled = robust_standardize(similarity_frame.to_numpy(dtype=float), similarity_columns)
    scaled = apply_feature_confidence_weights(scaled, similarity_columns)
    scaled = apply_group_weights(scaled, similarity_columns, similarity_feature_groups())
    euclidean = euclidean_distances(scaled)
    cosine = cosine_distances(scaled)
    np.fill_diagonal(euclidean, np.inf)
    np.fill_diagonal(cosine, np.inf)
    return euclidean, cosine


def transformed_similarity_features(frame: pd.DataFrame) -> pd.DataFrame:
    values_by_column = {column: frame[column].to_numpy(dtype=float) for column in FEATURE_COLUMNS}
    if all(column in values_by_column for column in HUE_COLUMNS):
        hue_values = np.column_stack([values_by_column[column] for column in HUE_COLUMNS])
        smoothed = circular_smooth_histogram(hue_values)
        for index, column in enumerate(HUE_COLUMNS):
            values_by_column[column] = smoothed[:, index]

    transformed: dict[str, np.ndarray] = {}
    for column in FEATURE_COLUMNS:
        if column == ORIENTATION_COLUMN:
            radians = np.deg2rad(values_by_column[column] * 2.0)
            confidence = np.clip(values_by_column[ORIENTATION_CONFIDENCE_COLUMN], 0.0, 1.0)
            confidence = np.where(
                confidence >= extract_icon_features.ORIENTATION_CONFIDENCE_THRESHOLD,
                confidence,
                0.0,
            )
            transformed[ORIENTATION_DERIVED_COLUMNS[0]] = np.cos(radians) * confidence
            transformed[ORIENTATION_DERIVED_COLUMNS[1]] = np.sin(radians) * confidence
        else:
            transformed[column] = values_by_column[column]
    return pd.DataFrame(transformed, columns=similarity_feature_columns())


def circular_smooth_histogram(values: np.ndarray) -> np.ndarray:
    return 0.50 * values + 0.25 * np.roll(values, 1, axis=1) + 0.25 * np.roll(values, -1, axis=1)


def similarity_feature_columns() -> list[str]:
    columns = []
    for column in FEATURE_COLUMNS:
        if column == ORIENTATION_COLUMN:
            columns.extend(ORIENTATION_DERIVED_COLUMNS)
        else:
            columns.append(column)
    return columns


def active_similarity_feature_columns() -> list[str]:
    grouped_columns = []
    for group_columns in similarity_feature_groups().values():
        grouped_columns.extend(group_columns)
    return grouped_columns


def similarity_feature_groups() -> dict[str, list[str]]:
    groups = {}
    for section in build_analysis_dashboard.image_feature_sections():
        group_columns = []
        for feature in section["features"]:
            feature_id = feature["id"]
            if feature_id == ORIENTATION_COLUMN:
                group_columns.extend(ORIENTATION_DERIVED_COLUMNS)
            else:
                group_columns.append(feature_id)
        groups[section["title"]] = group_columns
    return groups


def robust_standardize(values: np.ndarray, columns: list[str]) -> np.ndarray:
    scaled = np.zeros_like(values, dtype=float)
    for index, column in enumerate(columns):
        column_values = values[:, index]
        if column in BOUNDED_VECTOR_FEATURE_COLUMNS:
            scaled[:, index] = column_values
            continue
        if column in BINARY_FEATURE_COLUMNS:
            scaled[:, index] = column_values - float(np.nanmean(column_values))
            continue

        median = float(np.nanmedian(column_values))
        q25, q75 = np.nanpercentile(column_values, [25, 75])
        scale = float((q75 - q25) / 1.349)
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = float(np.nanstd(column_values))
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = 1.0
        scaled[:, index] = np.clip((column_values - median) / scale, -ROBUST_CLIP_Z, ROBUST_CLIP_Z)
    return scaled


def apply_feature_confidence_weights(values: np.ndarray, columns: list[str]) -> np.ndarray:
    weighted = values.copy()
    for index, column in enumerate(columns):
        weighted[:, index] *= FEATURE_CONFIDENCE_WEIGHTS.get(column, 1.0)
    return weighted


def apply_group_weights(values: np.ndarray, columns: list[str], groups: dict[str, list[str]] | list[list[str]]) -> np.ndarray:
    weighted = values.copy()
    column_index = {column: index for index, column in enumerate(columns)}
    group_items = groups.items() if isinstance(groups, dict) else [(None, group) for group in groups]
    for group_name, group in group_items:
        indices = [column_index[column] for column in group if column in column_index]
        if not indices:
            continue
        family_weight = FAMILY_RELIABILITY_WEIGHTS.get(str(group_name), 1.0)
        weighted[:, indices] *= family_weight / math.sqrt(len(indices))
    return weighted


def euclidean_distances(values: np.ndarray) -> np.ndarray:
    norms = (values**2).sum(axis=1)
    squared = norms[:, None] + norms[None, :] - 2 * values @ values.T
    return np.sqrt(np.maximum(squared, 0.0))


def cosine_distances(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1)
    safe = np.where(norms == 0, 1.0, norms)
    normalized = values / safe[:, None]
    similarity = normalized @ normalized.T
    return 1.0 - np.clip(similarity, -1.0, 1.0)


def write_distance_matrix(frame: pd.DataFrame, distances: np.ndarray, output: Path) -> None:
    matrix = pd.DataFrame(distances, index=frame["icon_id"], columns=frame["icon_id"])
    matrix.replace(np.inf, 0.0).to_csv(output)


def nearest_neighbor_rows(frame: pd.DataFrame, distances: np.ndarray, neighbors: int) -> list[dict]:
    rows = []
    for source_index, row in frame.iterrows():
        nearest_indices = np.argsort(distances[source_index])[:neighbors]
        for rank, target_index in enumerate(nearest_indices, start=1):
            target = frame.iloc[target_index]
            rows.append(pair_row(row, target, rank, distances[source_index, target_index]))
    return rows


def closest_pair_rows(
    frame: pd.DataFrame,
    distances: np.ndarray,
    limit: int,
    cross_set_only: bool = False,
    same_set_only: bool = False,
) -> list[dict]:
    candidates = []
    for i in range(len(frame)):
        for j in range(i + 1, len(frame)):
            if cross_set_only and frame.iloc[i]["set_id"] == frame.iloc[j]["set_id"]:
                continue
            if same_set_only and frame.iloc[i]["set_id"] != frame.iloc[j]["set_id"]:
                continue
            candidates.append((distances[i, j], i, j))
    candidates.sort(key=lambda item: item[0])
    return [
        pair_row(frame.iloc[i], frame.iloc[j], rank, distance)
        for rank, (distance, i, j) in enumerate(candidates[:limit], start=1)
    ]


def pair_row(source: pd.Series, target: pd.Series, rank: int, distance: float) -> dict:
    out = {
        "rank": rank,
        "distance": float(distance),
    }
    for prefix, item in [("source", source), ("target", target)]:
        for column in METADATA_COLUMNS:
            out[f"{prefix}_{column}"] = item[column]
    return out


def write_rows(rows: list[dict], output: Path) -> None:
    if not rows:
        output.write_text("", encoding="utf-8")
        return
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def create_pair_sheet(rows: list[dict], output: Path, title: str, limit: int = 24) -> None:
    selected = rows[:limit]
    columns = 4
    thumb = 72
    gap = 10
    label_height = 58
    pair_width = thumb * 2 + gap * 3
    cell_height = thumb + label_height + gap * 2
    row_count = math.ceil(len(selected) / columns)
    sheet = Image.new("RGB", (columns * pair_width, max(1, row_count) * cell_height + 34), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((gap, gap), title, fill=(20, 20, 20), font=font)

    for index, row in enumerate(selected):
        cell_x = (index % columns) * pair_width
        cell_y = 34 + (index // columns) * cell_height
        source = load_icon(ROOT / row["source_normalized_path"], thumb)
        target = load_icon(ROOT / row["target_normalized_path"], thumb)
        sheet.paste(source, (cell_x + gap, cell_y + gap))
        sheet.paste(target, (cell_x + thumb + gap * 2, cell_y + gap))
        draw.text(
            (cell_x + gap, cell_y + thumb + gap + 2),
            f"#{row['rank']} d={float(row['distance']):.3f}",
            fill=(30, 30, 30),
            font=font,
        )
        draw.text(
            (cell_x + gap, cell_y + thumb + gap + 16),
            short_label(row["source_label"], 22),
            fill=(80, 80, 80),
            font=font,
        )
        draw.text(
            (cell_x + gap, cell_y + thumb + gap + 30),
            short_label(row["target_label"], 22),
            fill=(80, 80, 80),
            font=font,
        )
    sheet.save(output)


def load_icon(path: Path, size: int) -> Image.Image:
    try:
        icon = Image.open(path).convert("RGBA")
    except Exception:
        icon = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    icon.thumbnail((size, size), Image.Resampling.LANCZOS)
    background = Image.new("RGBA", (size, size), "white")
    background.alpha_composite(icon, ((size - icon.width) // 2, (size - icon.height) // 2))
    return background.convert("RGB")


def short_label(value: str, limit: int) -> str:
    value = str(value)
    return value if len(value) <= limit else value[: limit - 1] + "..."


def write_metadata(output_dir: Path, frame: pd.DataFrame, neighbors: int, closest_pairs: int) -> Path:
    output = output_dir / "similarity_metadata.json"
    groups = similarity_feature_groups()
    metadata = {
        "feature_schema_version": extract_icon_features.FEATURE_SCHEMA_VERSION,
        "input": relative_label(FEATURES_CSV),
        "row_count": int(len(frame)),
        "feature_columns": FEATURE_COLUMNS,
        "similarity_feature_columns": similarity_feature_columns(),
        "active_similarity_feature_columns": active_similarity_feature_columns(),
        "excluded_feature_columns": sorted(build_analysis_dashboard.EXCLUDED_IMAGE_FEATURES),
        "excluded_feature_reasons": build_analysis_dashboard.EXCLUDED_IMAGE_FEATURE_REASONS,
        "preprocessing": [
            "principal_axis_orientation_v2 is encoded as cos/sin of doubled angle so 0 and 180 degrees compare as the same axis",
            "orientation vectors are scaled by orientation_confidence_v2 and set to zero below confidence 0.20",
            "hue histogram bins are circularly smoothed with wraparound before scaling",
            "binary flags are centered without variance expansion",
            "bounded circular vector features keep their native -1..1 scale",
        ],
        "standardization": f"column-wise robust median/IQR scaling clipped to +/-{ROBUST_CLIP_Z:g} before feature and family weighting",
        "feature_groups": groups,
        "extractor_feature_groups": {
            extractor.name: list(extractor.columns) for extractor in extract_icon_features.FEATURE_EXTRACTORS
        },
        "family_reliability_weights": FAMILY_RELIABILITY_WEIGHTS,
        "feature_confidence_weights": FEATURE_CONFIDENCE_WEIGHTS,
        "distance_metrics": ["euclidean", "cosine"],
        "neighbors_per_icon": neighbors,
        "closest_pair_limit": closest_pairs,
    }
    output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return output


def write_html_report(outputs: list[Path], csv_outputs: list[Path], metadata: Path, output_dir: Path) -> Path:
    image_blocks = "\n".join(
        f'<section><h2>{html.escape(path.stem.replace("_", " ").title())}</h2>'
        f'<img src="{html.escape(path.name)}" alt="{html.escape(path.stem)}"></section>'
        for path in outputs
    )
    csv_links = "\n".join(
        f'<li><a href="{html.escape(path.name)}">{html.escape(path.name)}</a></li>' for path in csv_outputs
    )
    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Icon Pairwise Similarity Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; color: #222; }}
    img {{ max-width: 100%; border: 1px solid #ddd; }}
    section {{ margin: 32px 0; }}
    code {{ background: #f5f5f5; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>Icon Pairwise Similarity Report</h1>
  <p>Metadata: <a href="{html.escape(metadata.name)}">{html.escape(metadata.name)}</a></p>
  <h2>CSV Outputs</h2>
  <ul>{csv_links}</ul>
  {image_blocks}
</body>
</html>
"""
    output = output_dir / "index.html"
    output.write_text(report, encoding="utf-8")
    return output


def relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute pairwise icon feature similarity.")
    parser.add_argument("--features", type=Path, default=FEATURES_CSV)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--neighbors", type=int, default=5)
    parser.add_argument("--closest-pairs", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global FEATURES_CSV
    FEATURES_CSV = args.features
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_features(args.features)
    euclidean, cosine = compute_distances(frame)

    euclidean_matrix = args.output_dir / "pairwise_distance_euclidean.csv"
    cosine_matrix = args.output_dir / "pairwise_distance_cosine.csv"
    write_distance_matrix(frame, euclidean, euclidean_matrix)
    write_distance_matrix(frame, cosine, cosine_matrix)

    nearest_rows = nearest_neighbor_rows(frame, euclidean, args.neighbors)
    all_pairs = closest_pair_rows(frame, euclidean, args.closest_pairs)
    cross_set_pairs = closest_pair_rows(frame, euclidean, args.closest_pairs, cross_set_only=True)
    same_set_pairs = closest_pair_rows(frame, euclidean, args.closest_pairs, same_set_only=True)

    nearest_csv = args.output_dir / "nearest_neighbors_euclidean.csv"
    closest_csv = args.output_dir / "closest_pairs_euclidean.csv"
    cross_set_csv = args.output_dir / "closest_cross_set_pairs_euclidean.csv"
    same_set_csv = args.output_dir / "closest_same_set_pairs_euclidean.csv"
    write_rows(nearest_rows, nearest_csv)
    write_rows(all_pairs, closest_csv)
    write_rows(cross_set_pairs, cross_set_csv)
    write_rows(same_set_pairs, same_set_csv)

    image_outputs = [
        args.output_dir / "closest_pairs_euclidean.png",
        args.output_dir / "closest_cross_set_pairs_euclidean.png",
        args.output_dir / "closest_same_set_pairs_euclidean.png",
    ]
    create_pair_sheet(all_pairs, image_outputs[0], "Closest feature-similar icon pairs")
    create_pair_sheet(cross_set_pairs, image_outputs[1], "Closest cross-set feature-similar icon pairs")
    create_pair_sheet(same_set_pairs, image_outputs[2], "Closest same-set feature-similar icon pairs")

    metadata = write_metadata(args.output_dir, frame, args.neighbors, args.closest_pairs)
    html_report = write_html_report(
        image_outputs,
        [nearest_csv, closest_csv, cross_set_csv, same_set_csv, euclidean_matrix, cosine_matrix],
        metadata,
        args.output_dir,
    )

    print(f"Wrote similarity report to {html_report}")
    for output in [metadata, nearest_csv, closest_csv, cross_set_csv, same_set_csv, euclidean_matrix, cosine_matrix, *image_outputs]:
        print(output)


if __name__ == "__main__":
    main()
