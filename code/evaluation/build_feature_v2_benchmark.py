#!/usr/bin/env python3
"""Build the frozen, unrated schema-v2 feature benchmark and release-gate status."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import extract_icon_features


ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "icon_data/analysis/features.csv"
OUTPUT = ROOT / "icon_data/analysis/feature_v2_benchmark.csv"
STATUS = ROOT / "icon_data/analysis/feature_v2_release_gate.json"
OVERLAY_DIR = ROOT / "icon_data/analysis/feature_v2_mask_overlays"

FAMILIES = {
    "complexity": "canny_edge_density",
    "closure": "enclosure_score_v2",
    "orientation": "principal_axis_orientation_v2",
    "fill": "solid_fill_ratio_v2",
    "symmetry": "horizontal_symmetry_v2",
    "saturation": "mean_saturation_v2",
    "texture": "local_texture_variation_v2",
}
RATING_COLUMNS = [
    "rater_1_judgment",
    "rater_2_judgment",
    "mask_rater_1_acceptable",
    "mask_rater_2_acceptable",
    "mask_rater_1_gross_inversion",
    "mask_rater_2_gross_inversion",
    "adjudication_notes",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def quintiles(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    values = np.array([float(row[column]) for row in rows], dtype=float)
    order = np.argsort(values, kind="stable")
    out: dict[str, int] = {}
    for rank, index in enumerate(order):
        out[rows[int(index)]["icon_id"]] = min(4, int(rank * 5 / max(len(rows), 1))) + 1
    return out


def balanced_family_sample(rows: list[dict[str, str]], column: str, count: int = 50) -> list[dict[str, str]]:
    by_quintile = quintiles(rows, column)
    buckets: dict[tuple[int, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        mode = "red" if float(row.get("strict_red_flag_v2") or 0) >= 0.5 else (
            "bw" if float(row.get("is_monochrome") or 0) >= 0.5 else "colored"
        )
        buckets[(by_quintile[row["icon_id"]], row["set_id"], mode)].append(row)
    for bucket in buckets.values():
        bucket.sort(key=lambda row: (row.get("mask_is_uncertain", ""), row["icon_id"]))

    chosen: list[dict[str, str]] = []
    used: set[str] = set()
    set_ids = sorted({row["set_id"] for row in rows})
    per_quintile = count // 5
    for quintile in range(1, 6):
        quintile_start = len(chosen)
        rotated_sets = set_ids[quintile - 1 :] + set_ids[: quintile - 1]
        while len(chosen) - quintile_start < per_quintile:
            progressed = False
            for set_id in rotated_sets:
                for mode in ("bw", "red", "colored"):
                    bucket = buckets[(quintile, set_id, mode)]
                    candidate = next((row for row in bucket if row["icon_id"] not in used), None)
                    if candidate is None:
                        continue
                    chosen.append(candidate)
                    used.add(candidate["icon_id"])
                    progressed = True
                    if len(chosen) - quintile_start == per_quintile:
                        break
                if len(chosen) - quintile_start == per_quintile:
                    break
            if not progressed:
                break
    set_counts = Counter(row["set_id"] for row in chosen)
    missing_sets = [set_id for set_id in set_ids if set_counts[set_id] == 0]
    for missing_set in missing_sets:
        replacement = next(
            (
                row
                for row in rows
                if row["set_id"] == missing_set and row["icon_id"] not in used
            ),
            None,
        )
        if replacement is None:
            continue
        replacement_quintile = by_quintile[replacement["icon_id"]]
        victim_index = next(
            (
                index
                for index, row in enumerate(chosen)
                if by_quintile[row["icon_id"]] == replacement_quintile and set_counts[row["set_id"]] > 1
            ),
            None,
        )
        if victim_index is None:
            continue
        victim = chosen[victim_index]
        used.remove(victim["icon_id"])
        set_counts[victim["set_id"]] -= 1
        chosen[victim_index] = replacement
        used.add(replacement["icon_id"])
        set_counts[missing_set] += 1
    for row in chosen:
        row["_quintile"] = str(by_quintile[row["icon_id"]])
    return chosen


def benchmark_row(row: dict[str, str], family: str, feature: str, index: int) -> dict[str, str]:
    split = "calibration" if index < 30 else "held_out"
    rating_instruction = (
        "angle_0_180_or_undefined"
        if family == "orientation"
        else ("red_or_not_red" if family == "strict_red" else "ordinal_1_to_5")
    )
    return {
        "benchmark_id": f"{family}-{index + 1:03d}",
        "family": family,
        "split": split,
        "rating_instruction": rating_instruction,
        "icon_id": row["icon_id"],
        "set_id": row["set_id"],
        "set_name": row["set_name"],
        "label": row.get("label", ""),
        "normalized_path": row["normalized_path"],
        "mask_overlay_path": f"icon_data/analysis/feature_v2_mask_overlays/{row['icon_id']}.png",
        "feature_column": feature,
        "feature_value": row[feature],
        "preliminary_quintile": row.get("_quintile", ""),
        "mask_mode": row.get("mask_mode", ""),
        "mask_coverage": row.get("mask_coverage", ""),
        "mask_border_contact": row.get("mask_border_contact", ""),
        "mask_confidence": row.get("mask_confidence", ""),
        "mask_is_uncertain": row.get("mask_is_uncertain", ""),
        "red_pixel_ratio_v2": row.get("red_pixel_ratio_v2", ""),
        "strict_red_flag_v2": row.get("strict_red_flag_v2", ""),
        "orientation_confidence_v2": row.get("orientation_confidence_v2", ""),
        **{column: "" for column in RATING_COLUMNS},
    }


def write_mask_overlay(row: dict[str, str], output_dir: Path) -> None:
    source = ROOT / row["normalized_path"]
    context = extract_icon_features.load_image(source, 245)
    original = np.asarray(Image.open(source).convert("RGB"), dtype=np.uint8)
    tinted = original.astype(np.float32)
    green = np.zeros_like(tinted)
    green[:, :, 1] = 255.0
    tinted[context.foreground] = 0.55 * tinted[context.foreground] + 0.45 * green[context.foreground]
    combined = np.concatenate([original, np.clip(tinted, 0, 255).astype(np.uint8)], axis=1)
    output_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(combined, "RGB").save(output_dir / f"{row['icon_id']}.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, default=FEATURES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--overlay-dir", type=Path, default=OVERLAY_DIR)
    parser.add_argument("--skip-overlays", action="store_true")
    args = parser.parse_args()
    rows = read_rows(args.features)
    benchmark: list[dict[str, str]] = []
    for family, feature in FAMILIES.items():
        selected = balanced_family_sample(rows, feature)
        benchmark.extend(benchmark_row(row.copy(), family, feature, index) for index, row in enumerate(selected))

    strict_candidates = sorted(
        (row for row in rows if float(row["strict_red_flag_v2"]) >= 0.5),
        key=lambda row: (-float(row["red_pixel_ratio_v2"]), row["icon_id"]),
    )[:50]
    near_misses = sorted(
        (row for row in rows if float(row["strict_red_flag_v2"]) < 0.5),
        key=lambda row: (abs(float(row["red_pixel_ratio_v2"]) - 0.90), row["icon_id"]),
    )[:50]
    red_candidates = [*strict_candidates, *near_misses]
    if len(red_candidates) < 100:
        used = {row["icon_id"] for row in red_candidates}
        red_candidates.extend(
            row
            for row in sorted(rows, key=lambda row: (abs(float(row["red_pixel_ratio_v2"]) - 0.90), row["icon_id"]))
            if row["icon_id"] not in used
        )
        red_candidates = red_candidates[:100]
    for index, row in enumerate(red_candidates):
        benchmark.append(benchmark_row(row.copy(), "strict_red", "red_pixel_ratio_v2", index))

    if not args.skip_overlays:
        rows_by_id = {row["icon_id"]: row for row in rows}
        for icon_id in sorted({row["icon_id"] for row in benchmark}):
            write_mask_overlay(rows_by_id[icon_id], args.overlay_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(benchmark[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(benchmark)
    status = {
        "feature_schema_version": 2,
        "status": "blocked_pending_two_rater_benchmark",
        "pilot_enabled": False,
        "benchmark_rows": len(benchmark),
        "family_rows": {family: sum(row["family"] == family for row in benchmark) for family in [*FAMILIES, "strict_red"]},
        "required_gates": {
            "weighted_inter_rater_kappa": 0.60,
            "held_out_scalar_spearman": 0.60,
            "orientation_median_axial_error_degrees_max": 15,
            "orientation_p90_axial_error_degrees_max": 30,
            "orientation_undefined_f1": 0.80,
            "strict_red_precision": 1.00,
            "strict_red_recall": 0.80,
            "acceptable_masks": 0.95,
            "gross_background_inversions": 0,
        },
        "note": "Engineering outputs are available for review, but no release gate can pass until two independent raters complete the frozen benchmark.",
    }
    STATUS.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(benchmark)} frozen benchmark rows to {args.output}")


if __name__ == "__main__":
    main()
