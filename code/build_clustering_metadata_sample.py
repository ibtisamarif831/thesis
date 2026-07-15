#!/usr/bin/env python3
"""Build the metadata sample used by clustering experiments."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "icon_data" / "analysis"
DATASET_PATH = ANALYSIS_DIR / "dataset.csv"
FEATURES_PATH = ANALYSIS_DIR / "features.csv"
OUTPUT_PATH = ANALYSIS_DIR / "clustering_metadata_sample.csv"
REPORT_PATH = ANALYSIS_DIR / "clustering_metadata_missing_report.json"
MCDOUGALL_RATINGS_PATH = (
    ROOT
    / "icon_data"
    / "iconsets"
    / "01_mcdougall_symbol_icon_set"
    / "metadata"
    / "mcdougall_ratings.csv"
)


TEXT_SPLIT_RE = re.compile(r"[^a-z0-9]+")
FEATURE_METADATA_COLUMNS = [
    "recognized_text",
    "recognized_text_source",
    "recognized_text_confidence",
    "ocr_text_raw",
    "ocr_text_confidence",
    "semantic_symbol_type",
    "semantic_identity_source",
    "semantic_is_arrow",
    "semantic_arrow_direction",
    "semantic_is_object",
    "semantic_object_label",
    "semantic_object_category",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_mcdougall_ratings() -> dict[str, dict[str, str]]:
    if not MCDOUGALL_RATINGS_PATH.exists():
        return {}
    rows = read_csv(MCDOUGALL_RATINGS_PATH)
    return {row["appendix_item"]: row for row in rows if row.get("appendix_item")}


def notes_value(notes: str, key: str) -> str:
    prefix = f"{key}="
    for part in (notes or "").split(";"):
        part = part.strip()
        if part.startswith(prefix):
            return part.removeprefix(prefix).strip()
    return ""


def text_tokens(*values: str) -> str:
    tokens: list[str] = []
    seen: set[str] = set()
    for value in values:
        for token in TEXT_SPLIT_RE.split((value or "").lower()):
            if len(token) < 2 or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return " ".join(tokens)


def infer_style_label(row: dict[str, str]) -> str:
    label = "unknown"
    set_id = row["set_id"]
    category = (row.get("category") or "").lower()
    notes = (row.get("notes") or "").lower()
    normalized_path = (row.get("normalized_path") or "").lower()

    if set_id in {
        "02_aiga_dot_symbol_signs",
        "03_mapbox_maki_icons",
        "04_ocha_humanitarian_icons",
        "08_ghs_hazard_pictograms",
        "09_universal_symbols_healthcare_webfont",
        "11_iso_7010_safety_signs",
        "12_iso_15223_medical_device_symbols",
        "13_usp_pictograms_manual",
    }:
        label = "pictogram_symbol"
    elif set_id == "10_openmoji":
        label = "emoji_color"
    elif set_id == "06_blissymbolics":
        label = "blissymbol"
    elif set_id == "05_mulberry_symbols":
        label = "aac_symbol"
    elif set_id == "07_arasaac_pictograms":
        label = "aac_pictogram"
    elif set_id == "01_mcdougall_symbol_icon_set":
        label = "interface_icon"

    if "flag" in category or "flag" in normalized_path:
        label = f"{label}_flag"
    if "outline" in notes:
        label = f"{label}_outline"
    return label


def infer_aiga_category(label: str) -> str:
    label_lower = label.lower().replace("-", " ")
    compact = label_lower.replace(" ", "")

    category_rules = [
        ("transportation", ["airtransportation", "bus", "taxi", "carrental", "rentalcar", "rail", "watertransportation", "groundtransportation", "heliport", "flights"]),
        ("directional/navigation", ["arrow", "left", "right", "up", "down", "forward"]),
        ("prohibition/regulatory", ["no smoking", "nosmoking", "no dogs", "nodogs", "no parking", "noparking", "no entry", "noentry"]),
        ("public facility/service", ["information", "telephone", "mail", "ticket", "cashier", "currencyexchange", "baggage", "lockers", "lostandfound", "litter", "waitingroom", "customs", "immigration", "passport"]),
        ("access/circulation", ["elevator", "escalator", "stairs", "exit"]),
        ("restroom/accessibility", ["toilet", "toilets", "women", "men", "unisex", "nursery"]),
        ("food/retail/service", ["restaurant", "bar", "coffee", "shop", "barber", "beauty", "coatcheck"]),
        ("safety/emergency", ["firstaid", "first aid", "fire extinguisher"]),
        ("lodging", ["hotel"]),
        ("parking", ["parking"]),
    ]
    for category, keywords in category_rules:
        if any(keyword in label_lower or keyword in compact for keyword in keywords):
            return f"aiga wayfinding / {category}"
    return "aiga wayfinding / general symbol"


def infer_mcdougall_category(label: str, rating: dict[str, str] | None) -> str:
    label_lower = label.lower()
    common_response = (rating or {}).get("common_response", "").lower()
    combined = f"{label_lower} {common_response}"

    category_rules = [
        ("computer/interface command", ["computer", "task", "archive", "zoom", "contrast", "print", "save", "file", "operator"]),
        ("industrial/technical equipment", ["condenser", "vent", "ignition", "control", "belt", "fabric", "process", "drive", "machine", "electric", "valve"]),
        ("transportation/travel", ["airborne", "baggage", "car", "bus", "train", "aircraft", "transport"]),
        ("health/medical", ["health", "medical", "hospital", "doctor"]),
        ("tools/objects", ["airbrush", "axe", "lockers", "balance", "radio"]),
        ("hazard/science", ["atomic", "chemical", "radiation", "danger"]),
        ("people/organization", ["troops", "operators", "service", "people"]),
    ]
    for category, keywords in category_rules:
        if any(keyword in combined for keyword in keywords):
            return f"mcdougall normed icon / {category}"
    return "mcdougall normed icon / uncategorized"


def main() -> None:
    dataset_rows = read_csv(DATASET_PATH)
    feature_rows = read_csv(FEATURES_PATH)
    dataset_by_id = {row["icon_id"]: row for row in dataset_rows}
    mcdougall_ratings = load_mcdougall_ratings()

    output_rows: list[dict[str, str]] = []
    missing_by_field: Counter[str] = Counter()
    missing_by_set: dict[str, Counter[str]] = defaultdict(Counter)
    unresolved_paths: list[dict[str, str]] = []

    for feature_row in feature_rows:
        icon_id = feature_row["icon_id"]
        dataset_row = dataset_by_id.get(icon_id)
        if dataset_row is None:
            raise ValueError(f"Feature row has no dataset row: {icon_id}")

        source_path = dataset_row["relative_path"]
        normalized_path = dataset_row["normalized_path"]
        category = dataset_row.get("category", "")
        notes = dataset_row.get("notes", "")
        label = dataset_row.get("label", "")
        set_id = dataset_row["set_id"]
        original_category = category
        category_source = "dataset.csv" if category else ""
        mcdougall_rating = None

        if set_id == "01_mcdougall_symbol_icon_set":
            appendix_item = notes_value(notes, "appendix_item")
            mcdougall_rating = mcdougall_ratings.get(appendix_item)
            if not category:
                category = infer_mcdougall_category(label, mcdougall_rating)
                category_source = "inferred_from_mcdougall_label_and_ratings"
            if mcdougall_rating:
                notes_parts = [part for part in [notes] if part]
                notes_parts.append(
                    "mcdougall_ratings="
                    f"concreteness:{mcdougall_rating.get('concreteness', '')},"
                    f"complexity:{mcdougall_rating.get('complexity', '')},"
                    f"familiarity:{mcdougall_rating.get('familiarity', '')},"
                    f"meaningfulness:{mcdougall_rating.get('meaningfulness', '')},"
                    f"semantic_distance:{mcdougall_rating.get('semantic_distance', '')},"
                    f"concept_agreement:{mcdougall_rating.get('concept_agreement', '')},"
                    f"name_agreement:{mcdougall_rating.get('name_agreement', '')},"
                    f"common_response:{mcdougall_rating.get('common_response', '')}"
                )
                notes = "; ".join(notes_parts)

        if set_id == "02_aiga_dot_symbol_signs" and not category:
            category = infer_aiga_category(label)
            category_source = "inferred_from_aiga_label"

        row = {
            "icon_id": icon_id,
            "set_id": set_id,
            "set_name": dataset_row["set_name"],
            "icon_name": label,
            "label": label,
            "category": category,
            "original_category": original_category,
            "category_source": category_source,
            "style_label": infer_style_label(dataset_row),
            "source": dataset_row.get("source", ""),
            "source_url": dataset_row.get("source_url", ""),
            "format": dataset_row.get("format", ""),
            "filename": dataset_row.get("filename", ""),
            "relative_path": source_path,
            "normalized_path": normalized_path,
            "notes": notes,
            "metadata_text": " | ".join(
                value for value in [label, category, dataset_row["set_name"], notes] if value
            ),
            "metadata_tokens": text_tokens(label, category, dataset_row["set_name"], notes),
            "mcdougall_concreteness": (mcdougall_rating or {}).get("concreteness", ""),
            "mcdougall_complexity": (mcdougall_rating or {}).get("complexity", ""),
            "mcdougall_familiarity": (mcdougall_rating or {}).get("familiarity", ""),
            "mcdougall_meaningfulness": (mcdougall_rating or {}).get("meaningfulness", ""),
            "mcdougall_semantic_distance": (mcdougall_rating or {}).get("semantic_distance", ""),
            "mcdougall_concept_agreement": (mcdougall_rating or {}).get("concept_agreement", ""),
            "mcdougall_name_agreement": (mcdougall_rating or {}).get("name_agreement", ""),
            "mcdougall_common_response": (mcdougall_rating or {}).get("common_response", ""),
            **{column: feature_row.get(column, "") for column in FEATURE_METADATA_COLUMNS},
            "has_category": str(bool(category)).lower(),
            "has_notes": str(bool(notes)).lower(),
            "source_path_exists": str((ROOT / source_path).exists()).lower(),
            "normalized_path_exists": str((ROOT / normalized_path).exists()).lower(),
        }

        for field in ["category", "notes", "source_url", "label"]:
            if not row.get(field, "").strip():
                missing_by_field[field] += 1
                missing_by_set[set_id][field] += 1
        for path_field in ["relative_path", "normalized_path"]:
            if not (ROOT / row[path_field]).exists():
                unresolved_paths.append({"icon_id": icon_id, "field": path_field, "path": row[path_field]})

        output_rows.append(row)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0].keys())
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    set_counts = Counter(row["set_id"] for row in output_rows)
    report = {
        "input_dataset": str(DATASET_PATH.relative_to(ROOT)),
        "input_features": str(FEATURES_PATH.relative_to(ROOT)),
        "output": str(OUTPUT_PATH.relative_to(ROOT)),
        "rows": len(output_rows),
        "set_counts": dict(sorted(set_counts.items())),
        "missing_by_field": dict(sorted(missing_by_field.items())),
        "missing_by_set": {key: dict(value) for key, value in sorted(missing_by_set.items())},
        "unresolved_paths": unresolved_paths,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({len(output_rows)} rows)")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
