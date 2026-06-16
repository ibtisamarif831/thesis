#!/usr/bin/env python3
"""Extract visual features from normalized icon images.

The feature registry is intentionally small and explicit: add a new feature by
subclassing FeatureExtractor and adding it to FEATURE_EXTRACTORS.
"""

import argparse
import csv
import json
import math
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "icon_data/analysis"
DATASET_CSV = ANALYSIS_DIR / "dataset.csv"
FEATURES_CSV = ANALYSIS_DIR / "features.csv"
FEATURE_FAILURES_JSON = ANALYSIS_DIR / "feature_failures.json"


@dataclass(frozen=True)
class ImageContext:
    path: Path
    alpha: np.ndarray
    gray: np.ndarray
    foreground: np.ndarray


class FeatureExtractor:
    name = ""
    columns: tuple[str, ...] = ()

    def extract(self, context: ImageContext) -> dict[str, float]:
        raise NotImplementedError


class ForegroundAreaRatio(FeatureExtractor):
    name = "foreground_area_ratio"
    columns = ("foreground_area_ratio",)

    def extract(self, context: ImageContext) -> dict[str, float]:
        return {self.columns[0]: float(context.foreground.mean())}


class CannyEdgeDensity(FeatureExtractor):
    name = "canny_edge_density"
    columns = ("canny_edge_density",)

    def extract(self, context: ImageContext) -> dict[str, float]:
        edges = canny_edges(context.gray, context.foreground)
        return {self.columns[0]: float(edges.mean())}


class ConnectedComponents(FeatureExtractor):
    name = "connected_components"
    columns = ("connected_components",)

    def extract(self, context: ImageContext) -> dict[str, float]:
        return {self.columns[0]: float(count_components(context.foreground))}


class QuadtreeStructuralVariability(FeatureExtractor):
    name = "quadtree_structural_variability"
    columns = (
        "quadtree_leaf_count",
        "quadtree_structural_variability",
        "quadtree_mean_leaf_size",
    )

    def extract(self, context: ImageContext) -> dict[str, float]:
        stats = quadtree_stats(context.foreground.astype(np.float32))
        return {
            "quadtree_leaf_count": float(stats["leaf_count"]),
            "quadtree_structural_variability": float(stats["structural_variability"]),
            "quadtree_mean_leaf_size": float(stats["mean_leaf_size"]),
        }


FEATURE_EXTRACTORS: tuple[FeatureExtractor, ...] = (
    ForegroundAreaRatio(),
    CannyEdgeDensity(),
    ConnectedComponents(),
    QuadtreeStructuralVariability(),
)


def load_rows(limit: int | None = None, per_set_limit: int | None = None) -> list[dict[str, str]]:
    with DATASET_CSV.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if per_set_limit is not None:
        rows = sample_per_set(rows, per_set_limit)
    return rows[:limit] if limit else rows


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


def load_image(path: Path, foreground_threshold: int) -> ImageContext:
    image = Image.open(path).convert("RGBA")
    data = np.asarray(image, dtype=np.float32)
    rgb = data[:, :, :3]
    alpha = data[:, :, 3] / 255.0

    # Use alpha when present, otherwise infer foreground from non-white pixels.
    if np.any(alpha < 0.99):
        foreground = alpha > (foreground_threshold / 255.0)
    else:
        foreground = np.any(rgb < foreground_threshold, axis=2)

    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) / 255.0
    gray = np.where(foreground, gray, 1.0)
    return ImageContext(path=path, alpha=alpha, gray=gray.astype(np.float32), foreground=foreground)


def gaussian_blur(image: np.ndarray) -> np.ndarray:
    kernel = np.array([1, 4, 6, 4, 1], dtype=np.float32) / 16.0
    padded = np.pad(image, ((0, 0), (2, 2)), mode="edge")
    horizontal = np.zeros_like(image, dtype=np.float32)
    for offset, weight in enumerate(kernel):
        horizontal += weight * padded[:, offset : offset + image.shape[1]]

    padded = np.pad(horizontal, ((2, 2), (0, 0)), mode="edge")
    vertical = np.zeros_like(image, dtype=np.float32)
    for offset, weight in enumerate(kernel):
        vertical += weight * padded[offset : offset + image.shape[0], :]
    return vertical


def convolve3(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    padded = np.pad(image, 1, mode="edge")
    out = np.zeros_like(image, dtype=np.float32)
    for y in range(3):
        for x in range(3):
            out += kernel[y, x] * padded[y : y + image.shape[0], x : x + image.shape[1]]
    return out


def canny_edges(gray: np.ndarray, foreground: np.ndarray) -> np.ndarray:
    if cv2 is not None:
        gray_u8 = np.clip(gray * 255.0, 0, 255).astype(np.uint8)
        blurred = cv2.GaussianBlur(gray_u8, (5, 5), 1.0)
        edges = cv2.Canny(blurred, 50, 150) > 0
        return edges & dilate(foreground)

    blurred = gaussian_blur(gray)
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
    gx = convolve3(blurred, sobel_x)
    gy = convolve3(blurred, sobel_y)
    magnitude = np.hypot(gx, gy)
    angle = (np.rad2deg(np.arctan2(gy, gx)) + 180.0) % 180.0

    suppressed = non_maximum_suppression(magnitude, angle)
    nonzero = suppressed[suppressed > 0]
    if nonzero.size == 0:
        return np.zeros_like(foreground, dtype=bool)

    high = max(float(np.percentile(nonzero, 85)), 0.08)
    low = high * 0.4
    edges = hysteresis_threshold(suppressed, low, high)
    return edges & dilate(foreground)


def non_maximum_suppression(magnitude: np.ndarray, angle: np.ndarray) -> np.ndarray:
    out = np.zeros_like(magnitude, dtype=np.float32)
    padded = np.pad(magnitude, 1, mode="constant")

    directions = np.zeros_like(angle, dtype=np.uint8)
    directions[((angle < 22.5) | (angle >= 157.5))] = 0
    directions[((angle >= 22.5) & (angle < 67.5))] = 45
    directions[((angle >= 67.5) & (angle < 112.5))] = 90
    directions[((angle >= 112.5) & (angle < 157.5))] = 135

    neighbor_pairs = {
        0: ((0, -1), (0, 1)),
        45: ((-1, 1), (1, -1)),
        90: ((-1, 0), (1, 0)),
        135: ((-1, -1), (1, 1)),
    }
    height, width = magnitude.shape
    for direction, ((dy1, dx1), (dy2, dx2)) in neighbor_pairs.items():
        mask = directions == direction
        n1 = padded[1 + dy1 : 1 + dy1 + height, 1 + dx1 : 1 + dx1 + width]
        n2 = padded[1 + dy2 : 1 + dy2 + height, 1 + dx2 : 1 + dx2 + width]
        keep = mask & (magnitude >= n1) & (magnitude >= n2)
        out[keep] = magnitude[keep]
    return out


def hysteresis_threshold(magnitude: np.ndarray, low: float, high: float) -> np.ndarray:
    strong = magnitude >= high
    weak = (magnitude >= low) & ~strong
    edges = strong.copy()
    queue = deque(zip(*np.nonzero(strong)))
    height, width = magnitude.shape

    while queue:
        y, x = queue.popleft()
        for yy in range(max(0, y - 1), min(height, y + 2)):
            for xx in range(max(0, x - 1), min(width, x + 2)):
                if weak[yy, xx] and not edges[yy, xx]:
                    edges[yy, xx] = True
                    queue.append((yy, xx))
    return edges


def dilate(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    out = np.zeros_like(mask, dtype=bool)
    for y in range(3):
        for x in range(3):
            out |= padded[y : y + mask.shape[0], x : x + mask.shape[1]]
    return out


def count_components(mask: np.ndarray) -> int:
    seen = np.zeros_like(mask, dtype=bool)
    height, width = mask.shape
    count = 0

    for start_y, start_x in zip(*np.nonzero(mask & ~seen)):
        if seen[start_y, start_x]:
            continue
        count += 1
        queue = deque([(int(start_y), int(start_x))])
        seen[start_y, start_x] = True
        while queue:
            y, x = queue.popleft()
            for yy in range(max(0, y - 1), min(height, y + 2)):
                for xx in range(max(0, x - 1), min(width, x + 2)):
                    if mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        queue.append((yy, xx))
    return count


def quadtree_stats(mask: np.ndarray, variance_threshold: float = 0.02, min_size: int = 4) -> dict[str, float]:
    leaves: list[int] = []
    stack = [(0, 0, mask.shape[0], mask.shape[1])]

    while stack:
        y, x, height, width = stack.pop()
        block = mask[y : y + height, x : x + width]
        if height <= min_size or width <= min_size or float(block.var()) <= variance_threshold:
            leaves.append(height * width)
            continue

        half_h = height // 2
        half_w = width // 2
        if half_h == 0 or half_w == 0:
            leaves.append(height * width)
            continue
        stack.extend(
            [
                (y, x, half_h, half_w),
                (y, x + half_w, half_h, width - half_w),
                (y + half_h, x, height - half_h, half_w),
                (y + half_h, x + half_w, height - half_h, width - half_w),
            ]
        )

    leaf_count = len(leaves)
    total_pixels = mask.size
    max_leaves = total_pixels / float(min_size * min_size)
    mean_leaf_size = sum(leaves) / float(leaf_count) if leaf_count else 0.0
    return {
        "leaf_count": leaf_count,
        "structural_variability": leaf_count / max_leaves if max_leaves else 0.0,
        "mean_leaf_size": mean_leaf_size,
    }


def extract_row(row: dict[str, str], extractors: tuple[FeatureExtractor, ...], foreground_threshold: int):
    normalized_path = ROOT / row["normalized_path"]
    if not normalized_path.exists():
        return None, {"icon_id": row["icon_id"], "error": f"missing normalized image: {row['normalized_path']}"}

    context = load_image(normalized_path, foreground_threshold)
    feature_values: dict[str, float | str] = {
        "icon_id": row["icon_id"],
        "set_id": row["set_id"],
        "set_name": row["set_name"],
        "label": row["label"],
        "category": row["category"],
        "normalized_path": row["normalized_path"],
    }
    for extractor in extractors:
        feature_values.update(extractor.extract(context))
    return feature_values, None


def write_features(rows: list[dict[str, float | str]], output: Path, extractors: tuple[FeatureExtractor, ...]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata_columns = ["icon_id", "set_id", "set_name", "label", "category", "normalized_path"]
    feature_columns = [column for extractor in extractors for column in extractor.columns]
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=metadata_columns + feature_columns)
        writer.writeheader()
        writer.writerows(rows)


def write_feature_metadata(
    output: Path,
    extractors: tuple[FeatureExtractor, ...],
    row_count: int,
    selected_row_count: int,
    per_set_limit: int | None,
) -> None:
    try:
        output_label = str(output.relative_to(ROOT))
    except ValueError:
        output_label = str(output)

    metadata = {
        "input": str(DATASET_CSV.relative_to(ROOT)),
        "output": output_label,
        "row_count": row_count,
        "selected_row_count": selected_row_count,
        "per_set_limit": per_set_limit,
        "dependencies": {
            "opencv_available": cv2 is not None,
            "opencv_version": getattr(cv2, "__version__", None) if cv2 is not None else None,
        },
        "features": [
            {
                "name": extractor.name,
                "columns": list(extractor.columns),
            }
            for extractor in extractors
        ],
    }
    (output.parent / "features_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract visual features from normalized icon PNGs.")
    parser.add_argument("--dataset", type=Path, default=DATASET_CSV)
    parser.add_argument("--output", type=Path, default=FEATURES_CSV)
    parser.add_argument("--failures", type=Path, default=FEATURE_FAILURES_JSON)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--per-set-limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--foreground-threshold", type=int, default=245)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global DATASET_CSV
    DATASET_CSV = args.dataset

    source_rows = load_rows(limit=args.limit, per_set_limit=args.per_set_limit)
    failures = []
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(extract_row, row, FEATURE_EXTRACTORS, args.foreground_threshold)
            for row in source_rows
        ]
        for index, future in enumerate(as_completed(futures), start=1):
            row, failure = future.result()
            if failure:
                failures.append(failure)
            else:
                results.append(row)
            if index % 1000 == 0:
                print(f"Extracted/checked {index}/{len(source_rows)}")

    results.sort(key=lambda item: str(item["icon_id"]))
    write_features(results, args.output, FEATURE_EXTRACTORS)
    write_feature_metadata(
        args.output,
        FEATURE_EXTRACTORS,
        len(results),
        len(source_rows),
        args.per_set_limit,
    )
    args.failures.write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(results)} feature rows to {args.output}")
    print(f"Feature extraction failures: {len(failures)}")


if __name__ == "__main__":
    main()
