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
    rgb: np.ndarray
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


class GeometryAndContourFeatures(FeatureExtractor):
    name = "geometry_and_contour"
    columns = (
        "bounding_box_occupancy",
        "bounding_box_aspect_ratio",
        "solidity",
        "centroid_distance_from_center",
        "horizontal_symmetry",
        "vertical_symmetry",
        "perimeter_area_ratio",
        "filled_vs_outline_proxy",
        "contour_count",
        "holes_count",
        "closed_contour_ratio",
    )

    def extract(self, context: ImageContext) -> dict[str, float]:
        stats = geometry_stats(context.foreground)
        contour_stats_values = contour_stats(context.foreground)
        return {
            **stats,
            **contour_stats_values,
        }


class LineOrientationFeatures(FeatureExtractor):
    name = "line_orientation_histogram"
    columns = (
        "line_orientation_0",
        "line_orientation_45",
        "line_orientation_90",
        "line_orientation_135",
    )

    def extract(self, context: ImageContext) -> dict[str, float]:
        return line_orientation_histogram(context.gray, context.foreground)


class ColorFeatures(FeatureExtractor):
    name = "color"
    columns = (
        "is_monochrome",
        "color_count",
        "mean_saturation",
        "colorfulness",
        "foreground_background_contrast",
    )

    def extract(self, context: ImageContext) -> dict[str, float]:
        return color_stats(context.rgb, context.gray, context.foreground)


class GridLayoutFeatures(FeatureExtractor):
    name = "grid_layout_4x4"
    columns = tuple(f"grid_foreground_{row}_{col}" for row in range(4) for col in range(4))

    def extract(self, context: ImageContext) -> dict[str, float]:
        return grid_foreground_stats(context.foreground, rows=4, cols=4)


FEATURE_EXTRACTORS: tuple[FeatureExtractor, ...] = (
    ForegroundAreaRatio(),
    CannyEdgeDensity(),
    ConnectedComponents(),
    QuadtreeStructuralVariability(),
    GeometryAndContourFeatures(),
    LineOrientationFeatures(),
    ColorFeatures(),
    GridLayoutFeatures(),
)

FEATURE_COLUMNS: tuple[str, ...] = tuple(column for extractor in FEATURE_EXTRACTORS for column in extractor.columns)
FEATURE_GROUPS: tuple[tuple[str, ...], ...] = tuple(extractor.columns for extractor in FEATURE_EXTRACTORS)


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
    return ImageContext(
        path=path,
        rgb=(rgb / 255.0).astype(np.float32),
        alpha=alpha,
        gray=gray.astype(np.float32),
        foreground=foreground,
    )


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


def geometry_stats(mask: np.ndarray) -> dict[str, float]:
    height, width = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return {
            "bounding_box_occupancy": 0.0,
            "bounding_box_aspect_ratio": 0.0,
            "solidity": 0.0,
            "centroid_distance_from_center": 0.0,
            "horizontal_symmetry": 1.0,
            "vertical_symmetry": 1.0,
        }

    min_x, max_x = int(xs.min()), int(xs.max())
    min_y, max_y = int(ys.min()), int(ys.max())
    bbox_width = max_x - min_x + 1
    bbox_height = max_y - min_y + 1
    bbox_area = bbox_width * bbox_height
    foreground_area = int(mask.sum())
    centroid_x = float(xs.mean()) / max(width - 1, 1)
    centroid_y = float(ys.mean()) / max(height - 1, 1)
    center_distance = math.hypot(centroid_x - 0.5, centroid_y - 0.5) / math.hypot(0.5, 0.5)

    return {
        "bounding_box_occupancy": float(foreground_area / bbox_area) if bbox_area else 0.0,
        "bounding_box_aspect_ratio": float(bbox_width / bbox_height) if bbox_height else 0.0,
        "solidity": convex_solidity(mask),
        "centroid_distance_from_center": float(center_distance),
        "horizontal_symmetry": symmetry_score(mask, axis="horizontal"),
        "vertical_symmetry": symmetry_score(mask, axis="vertical"),
    }


def convex_solidity(mask: np.ndarray) -> float:
    foreground_area = float(mask.sum())
    if foreground_area == 0:
        return 0.0
    points = np.column_stack(np.nonzero(mask)).astype(np.int32)
    if len(points) < 3:
        return 1.0
    if cv2 is None:
        boundary = boundary_points(mask)
        hull = convex_hull(boundary)
        hull_area = polygon_area(hull)
        if hull_area <= 0:
            return 1.0
        return float(min(foreground_area / hull_area, 1.0))
    points_xy = points[:, ::-1]
    hull = cv2.convexHull(points_xy)
    hull_area = float(cv2.contourArea(hull))
    if hull_area <= 0:
        return 1.0
    return float(min(foreground_area / hull_area, 1.0))


def symmetry_score(mask: np.ndarray, axis: str) -> float:
    flipped = np.fliplr(mask) if axis == "horizontal" else np.flipud(mask)
    union = mask | flipped
    if not union.any():
        return 1.0
    overlap = mask & flipped
    return float(overlap.sum() / union.sum())


def contour_stats(mask: np.ndarray) -> dict[str, float]:
    foreground_area = float(mask.sum())
    if foreground_area == 0:
        return {
            "perimeter_area_ratio": 0.0,
            "filled_vs_outline_proxy": 0.0,
            "contour_count": 0.0,
            "holes_count": 0.0,
            "closed_contour_ratio": 0.0,
        }

    if cv2 is None:
        perimeter = mask_perimeter(mask)
        contour_count = float(count_components(mask))
        holes_count = float(count_holes(mask))
        perimeter_area_ratio = float(perimeter / foreground_area)
        filled_proxy = float(foreground_area / max(foreground_area + perimeter, 1.0))
        closed_contour_ratio = closed_contour_proxy(perimeter_area_ratio, contour_count, holes_count)
        return {
            "perimeter_area_ratio": perimeter_area_ratio,
            "filled_vs_outline_proxy": filled_proxy,
            "contour_count": contour_count,
            "holes_count": holes_count,
            "closed_contour_ratio": closed_contour_ratio,
        }

    binary = (mask.astype(np.uint8) * 255)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {
            "perimeter_area_ratio": 0.0,
            "filled_vs_outline_proxy": 0.0,
            "contour_count": 0.0,
            "holes_count": 0.0,
            "closed_contour_ratio": 0.0,
        }

    hierarchy_array = hierarchy[0] if hierarchy is not None else np.empty((0, 4), dtype=np.int32)
    external_indices = [index for index, item in enumerate(hierarchy_array) if item[3] < 0]
    hole_indices = [index for index, item in enumerate(hierarchy_array) if item[3] >= 0]
    external_contours = [contours[index] for index in external_indices] or contours
    perimeter = float(sum(cv2.arcLength(contour, True) for contour in external_contours))
    contour_count = float(len(external_contours))
    holes_count = float(len(hole_indices))
    perimeter_area_ratio = float(perimeter / foreground_area)
    filled_proxy = float(foreground_area / max(foreground_area + perimeter, 1.0))
    closed_contour_ratio = closed_contour_proxy(perimeter_area_ratio, contour_count, holes_count)

    return {
        "perimeter_area_ratio": perimeter_area_ratio,
        "filled_vs_outline_proxy": filled_proxy,
        "contour_count": contour_count,
        "holes_count": holes_count,
        "closed_contour_ratio": closed_contour_ratio,
    }


def closed_contour_proxy(perimeter_area_ratio: float, contour_count: float, holes_count: float) -> float:
    hole_signal = min(holes_count / max(contour_count, 1.0), 1.0)
    compact_signal = 1.0 / (1.0 + 8.0 * max(perimeter_area_ratio, 0.0))
    return float(max(hole_signal, compact_signal))


def mask_perimeter(mask: np.ndarray) -> float:
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    center = padded[1:-1, 1:-1]
    exposed = (
        (center & ~padded[:-2, 1:-1]).astype(np.int16)
        + (center & ~padded[2:, 1:-1]).astype(np.int16)
        + (center & ~padded[1:-1, :-2]).astype(np.int16)
        + (center & ~padded[1:-1, 2:]).astype(np.int16)
    )
    return float(exposed.sum())


def boundary_points(mask: np.ndarray) -> list[tuple[int, int]]:
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    center = padded[1:-1, 1:-1]
    boundary = center & (
        ~padded[:-2, 1:-1] | ~padded[2:, 1:-1] | ~padded[1:-1, :-2] | ~padded[1:-1, 2:]
    )
    ys, xs = np.nonzero(boundary)
    return [(int(x), int(y)) for y, x in zip(ys, xs)]


def count_holes(mask: np.ndarray) -> int:
    background = ~mask
    if not background.any():
        return 0

    outside = np.zeros_like(background, dtype=bool)
    outside[0, :] = background[0, :]
    outside[-1, :] = background[-1, :]
    outside[:, 0] |= background[:, 0]
    outside[:, -1] |= background[:, -1]

    while True:
        expanded = dilate(outside) & background
        if np.array_equal(expanded, outside):
            break
        outside = expanded

    holes_mask = background & ~outside
    return count_components(holes_mask) if holes_mask.any() else 0


def convex_hull(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(origin: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower: list[tuple[int, int]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper: list[tuple[int, int]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


def polygon_area(points: list[tuple[int, int]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def line_orientation_histogram(gray: np.ndarray, foreground: np.ndarray) -> dict[str, float]:
    if not foreground.any():
        return {
            "line_orientation_0": 0.0,
            "line_orientation_45": 0.0,
            "line_orientation_90": 0.0,
            "line_orientation_135": 0.0,
        }
    blurred = gaussian_blur(gray)
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
    gx = convolve3(blurred, sobel_x)
    gy = convolve3(blurred, sobel_y)
    magnitude = np.hypot(gx, gy)
    threshold = np.percentile(magnitude[foreground], 75) if np.any(magnitude[foreground] > 0) else 0.0
    active = foreground & (magnitude > threshold)
    if not active.any():
        active = foreground & (magnitude > 0)
    if not active.any():
        return {
            "line_orientation_0": 0.0,
            "line_orientation_45": 0.0,
            "line_orientation_90": 0.0,
            "line_orientation_135": 0.0,
        }

    # Edge gradient is perpendicular to stroke direction.
    orientations = (np.rad2deg(np.arctan2(gy, gx)) + 90.0) % 180.0
    bins = {
        "line_orientation_0": ((orientations < 22.5) | (orientations >= 157.5)),
        "line_orientation_45": ((orientations >= 22.5) & (orientations < 67.5)),
        "line_orientation_90": ((orientations >= 67.5) & (orientations < 112.5)),
        "line_orientation_135": ((orientations >= 112.5) & (orientations < 157.5)),
    }
    weights = magnitude * active
    total = float(weights.sum())
    if total <= 0:
        return {key: 0.0 for key in bins}
    return {key: float(weights[mask].sum() / total) for key, mask in bins.items()}


def color_stats(rgb: np.ndarray, gray: np.ndarray, foreground: np.ndarray) -> dict[str, float]:
    if not foreground.any():
        return {
            "is_monochrome": 1.0,
            "color_count": 0.0,
            "mean_saturation": 0.0,
            "colorfulness": 0.0,
            "foreground_background_contrast": 0.0,
        }

    fg_rgb = rgb[foreground]
    saturation = saturation_values(fg_rgb)
    quantized = np.floor(np.clip(fg_rgb, 0, 1) * 7).astype(np.int16)
    colors = np.unique(quantized, axis=0)
    color_count = float(len(colors))
    mean_saturation = float(saturation.mean()) if len(saturation) else 0.0
    saturation_p95 = float(np.percentile(saturation, 95)) if len(saturation) else 0.0
    colorfulness_value = colorfulness(fg_rgb)
    is_monochrome = 1.0 if saturation_p95 < 0.08 and colorfulness_value < 0.05 else 0.0

    fg_gray = gray[foreground]
    bg_gray = gray[~foreground]
    if len(bg_gray):
        contrast = abs(float(fg_gray.mean()) - float(bg_gray.mean()))
    else:
        contrast = float(fg_gray.std()) if len(fg_gray) else 0.0

    return {
        "is_monochrome": is_monochrome,
        "color_count": color_count,
        "mean_saturation": mean_saturation,
        "colorfulness": colorfulness_value,
        "foreground_background_contrast": contrast,
    }


def saturation_values(rgb_values: np.ndarray) -> np.ndarray:
    max_channel = rgb_values.max(axis=1)
    min_channel = rgb_values.min(axis=1)
    saturation = np.zeros_like(max_channel)
    np.divide(max_channel - min_channel, max_channel, out=saturation, where=max_channel > 0)
    return saturation


def colorfulness(rgb_values: np.ndarray) -> float:
    if len(rgb_values) == 0:
        return 0.0
    values = rgb_values * 255.0
    red, green, blue = values[:, 0], values[:, 1], values[:, 2]
    rg = red - green
    yb = 0.5 * (red + green) - blue
    std_root = math.sqrt(float(rg.std() ** 2 + yb.std() ** 2))
    mean_root = math.sqrt(float(rg.mean() ** 2 + yb.mean() ** 2))
    return float((std_root + 0.3 * mean_root) / 255.0)


def grid_foreground_stats(mask: np.ndarray, rows: int, cols: int) -> dict[str, float]:
    height, width = mask.shape
    out: dict[str, float] = {}
    for row in range(rows):
        y0 = round(row * height / rows)
        y1 = round((row + 1) * height / rows)
        for col in range(cols):
            x0 = round(col * width / cols)
            x1 = round((col + 1) * width / cols)
            cell = mask[y0:y1, x0:x1]
            out[f"grid_foreground_{row}_{col}"] = float(cell.mean()) if cell.size else 0.0
    return out


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
