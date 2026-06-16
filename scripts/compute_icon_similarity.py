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
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
FEATURES_CSV = ROOT / "icon_data/analysis/features.csv"
OUTPUT_DIR = ROOT / "icon_data/analysis/similarity"

FEATURE_COLUMNS = [
    "foreground_area_ratio",
    "canny_edge_density",
    "connected_components",
    "quadtree_leaf_count",
    "quadtree_structural_variability",
    "quadtree_mean_leaf_size",
]

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
    scaled = StandardScaler().fit_transform(frame[FEATURE_COLUMNS].to_numpy(dtype=float))
    euclidean = pairwise_distances(scaled, metric="euclidean")
    cosine = pairwise_distances(scaled, metric="cosine")
    np.fill_diagonal(euclidean, np.inf)
    np.fill_diagonal(cosine, np.inf)
    return euclidean, cosine


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
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
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
    metadata = {
        "input": relative_label(FEATURES_CSV),
        "row_count": int(len(frame)),
        "feature_columns": FEATURE_COLUMNS,
        "standardization": "StandardScaler over feature columns",
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
