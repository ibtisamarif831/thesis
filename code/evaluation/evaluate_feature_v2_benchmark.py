#!/usr/bin/env python3
"""Evaluate the frozen two-rater v2 benchmark and enforce the all-family gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "icon_data/analysis/feature_v2_benchmark.csv"
OUTPUT = ROOT / "icon_data/analysis/feature_v2_release_gate.json"
ORDINAL_FAMILIES = {"complexity", "closure", "fill", "symmetry", "saturation", "texture"}


def weighted_kappa(left: np.ndarray, right: np.ndarray, categories: int = 5) -> float:
    observed = np.zeros((categories, categories), dtype=float)
    for a, b in zip(left.astype(int), right.astype(int)):
        observed[a - 1, b - 1] += 1
    observed /= max(observed.sum(), 1.0)
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0))
    indices = np.arange(categories)
    weights = ((indices[:, None] - indices[None, :]) / max(categories - 1, 1)) ** 2
    denominator = float((weights * expected).sum())
    return 1.0 - float((weights * observed).sum()) / denominator if denominator else 1.0


def ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    out = np.empty(len(values), dtype=float)
    index = 0
    while index < len(values):
        end = index + 1
        while end < len(values) and values[order[end]] == values[order[index]]:
            end += 1
        out[order[index:end]] = (index + end - 1) / 2.0
        index = end
    return out


def spearman(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2:
        return float("nan")
    return float(np.corrcoef(ranks(left), ranks(right))[0, 1])


def axial_error(first: float, second: float) -> float:
    difference = abs(first - second) % 180.0
    return min(difference, 180.0 - difference)


def axial_mean(values: list[float]) -> float:
    radians = np.deg2rad(np.asarray(values, dtype=float) * 2.0)
    return float((np.rad2deg(math.atan2(float(np.sin(radians).sum()), float(np.cos(radians).sum()))) / 2.0) % 180.0)


def f1_score(expected: np.ndarray, predicted: np.ndarray) -> float:
    tp = int(np.sum(expected & predicted))
    fp = int(np.sum(~expected & predicted))
    fn = int(np.sum(expected & ~predicted))
    return 2 * tp / max(2 * tp + fp + fn, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=BENCHMARK)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    with args.benchmark.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = ("rater_1_judgment", "rater_2_judgment")
    if any(not row[column].strip() for row in rows for column in required):
        pending = {
            "feature_schema_version": 2,
            "status": "blocked_pending_two_rater_benchmark",
            "pilot_enabled": False,
            "benchmark_rows": len(rows),
            "unrated_cells": sum(not row[column].strip() for row in rows for column in required),
        }
        args.output.write_text(json.dumps(pending, indent=2) + "\n", encoding="utf-8")
        print("Benchmark is incomplete; pilot remains blocked.")
        return

    metrics: dict[str, dict[str, float]] = {}
    passes: list[bool] = []
    for family in sorted(ORDINAL_FAMILIES):
        family_rows = [row for row in rows if row["family"] == family]
        left = np.array([float(row["rater_1_judgment"]) for row in family_rows])
        right = np.array([float(row["rater_2_judgment"]) for row in family_rows])
        kappa = weighted_kappa(left, right)
        held = [row for row in family_rows if row["split"] == "held_out"]
        feature = np.array([float(row["feature_value"]) for row in held])
        judgment = np.array([(float(row["rater_1_judgment"]) + float(row["rater_2_judgment"])) / 2 for row in held])
        correlation = spearman(feature, judgment)
        metrics[family] = {"weighted_kappa": kappa, "held_out_spearman": correlation}
        passes.append(kappa >= 0.60 and correlation >= 0.60)

    orientation = [row for row in rows if row["family"] == "orientation" and row["split"] == "held_out"]
    errors = []
    expected_undefined = []
    predicted_undefined = []
    for row in orientation:
        ratings = [row["rater_1_judgment"].strip().lower(), row["rater_2_judgment"].strip().lower()]
        human_undefined = all(value == "undefined" for value in ratings)
        machine_undefined = float(row.get("orientation_confidence_v2") or 0.0) < 0.20
        expected_undefined.append(human_undefined)
        predicted_undefined.append(machine_undefined)
        if not human_undefined and all(value != "undefined" for value in ratings):
            reference = axial_mean([float(ratings[0]), float(ratings[1])])
            errors.append(axial_error(float(row["feature_value"]), reference))
    median_error = float(np.median(errors)) if errors else math.inf
    p90_error = float(np.percentile(errors, 90)) if errors else math.inf
    undefined_f1 = f1_score(np.array(expected_undefined), np.array(predicted_undefined))
    metrics["orientation"] = {"median_axial_error": median_error, "p90_axial_error": p90_error, "undefined_f1": undefined_f1}
    passes.append(median_error <= 15 and p90_error <= 30 and undefined_f1 >= 0.80)

    red_rows = [row for row in rows if row["family"] == "strict_red"]
    expected_red = np.array([
        row["rater_1_judgment"].strip().lower() == "red" and row["rater_2_judgment"].strip().lower() == "red"
        for row in red_rows
    ])
    predicted_red = np.array([float(row["strict_red_flag_v2"]) >= 0.5 for row in red_rows])
    true_positive = int(np.sum(expected_red & predicted_red))
    precision = true_positive / max(int(np.sum(predicted_red)), 1)
    recall = true_positive / max(int(np.sum(expected_red)), 1)
    metrics["strict_red"] = {"precision": precision, "recall": recall}
    passes.append(precision == 1.0 and recall >= 0.80)

    mask_columns = (
        "mask_rater_1_acceptable",
        "mask_rater_2_acceptable",
        "mask_rater_1_gross_inversion",
        "mask_rater_2_gross_inversion",
    )
    mask_rows = [row for row in rows if all(row.get(column, "").strip() for column in mask_columns)]
    mask_acceptance = sum(
        row["mask_rater_1_acceptable"].lower() == "true" and row["mask_rater_2_acceptable"].lower() == "true"
        for row in mask_rows
    ) / max(len(mask_rows), 1)
    metrics["masks"] = {"two_rater_acceptance": mask_acceptance}
    gross_inversions = sum(
        row.get(column, "").strip().lower() == "true"
        for row in rows
        for column in ("mask_rater_1_gross_inversion", "mask_rater_2_gross_inversion")
    )
    metrics["masks"]["gross_background_inversions"] = gross_inversions
    passes.append(len(mask_rows) == len(rows) and mask_acceptance >= 0.95 and gross_inversions == 0)

    status = "passed" if all(passes) else "failed"
    result = {"feature_schema_version": 2, "status": status, "pilot_enabled": status == "passed", "metrics": metrics}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Feature-v2 release gate: {status}")


if __name__ == "__main__":
    main()
