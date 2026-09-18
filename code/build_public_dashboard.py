#!/usr/bin/env python3
"""Build the scoped public dashboard and study-selection web assets."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

from build_analysis_dashboard import DASHBOARD_SETS, DASHBOARD_SET_IDS


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "icon_data" / "analysis" / "analysis_dashboard"
OUTPUT_DIR = ROOT / "dist" / "dashboard"
DATASET_PATH = ROOT / "icon_data" / "analysis" / "dataset.csv"
AI_DATABASE_PATH = ROOT / "icon_data" / "analysis" / "ai_clustering" / "ai_clustering.sqlite3"
STUDY_SELECTION_SOURCE_DIR = ROOT / "web" / "study-selection"
STUDY_SELECTION_SEED_PATH = ROOT / "tmp" / "study_selection_icons.sql"

SOURCE_DETAILS = (
    {
        "set_id": "02_aiga_dot_symbol_signs",
        "name": "AIGA/DOT Symbol Signs",
        "source": "https://commons.wikimedia.org/wiki/Category:AIGA_symbol_signs",
        "license": "No standalone license file is present in the local source snapshot; consult each Wikimedia Commons file page before reuse outside this research dashboard.",
        "license_file": None,
    },
    {
        "set_id": "04_ocha_humanitarian_icons",
        "name": "OCHA Humanitarian Icons",
        "source": "https://github.com/mapaction/ocha-humanitarian-icons-for-gis",
        "license": "Created by UN OCHA with MapAction support. No standalone license file is present in the local source snapshot; verify the upstream reuse terms.",
        "license_file": None,
    },
    {
        "set_id": "09_universal_symbols_healthcare_webfont",
        "name": "Universal Symbols Healthcare Webfont",
        "source": "https://github.com/samcome/webfont-medical-icons",
        "license": "MIT License, copyright Samuel Fremondiere (2014).",
        "license_file": ROOT / "icon_data" / "iconsets" / "09_universal_symbols_healthcare_webfont" / "LICENSE",
    },
    {
        "set_id": "11_iso_7010_safety_signs",
        "name": "ISO 7010 Safety Signs",
        "source": "https://github.com/Adewra/ISO7010-Font",
        "license": "The local upstream snapshot contains GNU GPL version 3. It is a public implementation, not an official ISO distribution.",
        "license_file": ROOT / "icon_data" / "iconsets" / "11_iso_7010_safety_signs" / "LICENSE",
    },
    {
        "set_id": "12_iso_15223_medical_device_symbols",
        "name": "ISO 15223 Medical Device Symbols",
        "source": "https://github.com/t4dhg/medical-device-symbols",
        "license": "MIT License (2025). It is a public implementation, not an official ISO distribution.",
        "license_file": ROOT / "icon_data" / "iconsets" / "12_iso_15223_medical_device_symbols" / "LICENSE",
    },
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rewrite_normalized_paths(value):
    if isinstance(value, dict):
        return {key: rewrite_normalized_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_normalized_paths(item) for item in value]
    if isinstance(value, str) and value.startswith("../../normalized_256/"):
        return value.removeprefix("../../")
    return value


def load_scoped_dataset_rows() -> list[dict[str, str]]:
    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["set_id"] in DASHBOARD_SET_IDS]
    counts = Counter(row["set_id"] for row in rows)
    missing = DASHBOARD_SET_IDS - counts.keys()
    if missing:
        raise ValueError(f"Missing scoped datasets: {', '.join(sorted(missing))}")
    if len(rows) != 649:
        raise ValueError(f"Expected 649 scoped normalized images, found {len(rows)}")
    return rows


def export_compatible_ai_runs(eligible_icon_ids: set[str]) -> dict:
    runs: list[dict] = []
    details: dict[str, dict] = {}
    total_runs = 0
    if AI_DATABASE_PATH.exists():
        connection = sqlite3.connect(AI_DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        run_rows = connection.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
        total_runs = len(run_rows)
        for row in run_rows:
            item_rows = connection.execute(
                "SELECT * FROM run_items WHERE run_id=? ORDER BY item_order", (row["run_id"],)
            ).fetchall()
            item_ids = {item["icon_id"] for item in item_rows}
            if row["status"] != "completed" or not item_ids or not item_ids <= eligible_icon_ids:
                continue
            run = {key: row[key] for key in row.keys() if key not in {"metrics_json", "usage_json"}}
            run["metrics"] = json.loads(row["metrics_json"]) if row["metrics_json"] else None
            run["usage"] = json.loads(row["usage_json"]) if row["usage_json"] else None
            detail = dict(run)
            detail["items"] = [
                {key: item[key] for key in item.keys() if key not in {"run_id", "item_order"}}
                for item in item_rows
            ]
            runs.append(run)
            details[row["run_id"]] = detail
        connection.close()
    return {
        "status": {
            "configured": False,
            "public_read_only": True,
            "model_id": "Read-only archive",
            "cached_embeddings": 0,
            "saved_runs": len(runs),
            "message": (
                "Public read-only edition. New provider requests are disabled. "
                + (f"{len(runs)} compatible saved run(s) are available." if runs else "No saved AI runs match the five-dataset scope.")
            ),
        },
        "runs": runs[:20],
        "run_details": details,
        "source_run_count": total_runs,
        "excluded_incompatible_run_count": total_runs - len(runs),
    }


def credits_html(counts: Counter) -> str:
    cards = []
    for detail in SOURCE_DETAILS:
        license_link = ""
        if detail["license_file"]:
            license_link = f' <a href="licenses/{html.escape(detail["set_id"])}.txt">Full license text</a>.'
        cards.append(
            "<section><h2>"
            + html.escape(detail["name"])
            + f" <small>({counts[detail['set_id']]} images)</small></h2>"
            + f'<p><a href="{html.escape(detail["source"])}">Upstream source</a></p>'
            + f"<p>{html.escape(detail['license'])}{license_link}</p></section>"
        )
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Data sources and licenses</title><style>body{font:16px/1.55 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#18202f}a{color:#3156a3}section{border-top:1px solid #d9dee8;padding:16px 0}small{font-weight:400;color:#5d6675}.notice{background:#fff6d8;border:1px solid #ead28b;padding:14px;border-radius:8px}</style></head><body><p><a href="index.html">Back to dashboard</a></p><h1>Data sources and licenses</h1><p>This public research dashboard contains normalized 256 x 256 derivatives from five scoped source collections. Dataset names describe provenance and do not imply endorsement by AIGA, DOT, UN OCHA, ISO, or upstream maintainers.</p><p class="notice"><strong>Reuse note:</strong> the local AIGA and OCHA snapshots do not contain standalone license files. Their images are included here for the thesis demonstration with source attribution; verify upstream file-level terms before redistributing them elsewhere.</p>""" + "".join(cards) + "</body></html>"


def write_study_selection_assets(rows: list[dict[str, str]]) -> None:
    rows_by_set: dict[str, list[dict[str, str]]] = {set_id: [] for set_id, _ in DASHBOARD_SETS}
    for row in rows:
        rows_by_set[row["set_id"]].append(
            {
                "icon_id": row["icon_id"],
                "label": row.get("label", ""),
                "normalized_path": row["normalized_path"].removeprefix("icon_data/"),
            }
        )
    data = {
        "selection_version": "five-sets-20-v1",
        "required_per_set": 20,
        "sets": [
            {
                "set_id": set_id,
                "set_name": set_name,
                "icons": sorted(rows_by_set[set_id], key=lambda row: (row["label"].casefold(), row["icon_id"])),
            }
            for set_id, set_name in DASHBOARD_SETS
        ],
    }
    (OUTPUT_DIR / "study_selection_data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    for source in STUDY_SELECTION_SOURCE_DIR.iterdir():
        if source.is_file():
            target_name = "study-selection.html" if source.name == "index.html" else source.name
            shutil.copy2(source, OUTPUT_DIR / target_name)

    STUDY_SELECTION_SEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    values = []
    for row in rows:
        escaped = [str(row.get(key, "")).replace("'", "''") for key in ("icon_id", "set_id", "label")]
        values.append("('" + "','".join(escaped) + "')")
    STUDY_SELECTION_SEED_PATH.write_text(
        "DELETE FROM study_icons;\nINSERT INTO study_icons (icon_id,set_id,label) VALUES\n"
        + ",\n".join(values)
        + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    payload = read_json(SOURCE_DIR / "dashboard_data.json")
    expected_ids = [set_id for set_id, _ in DASHBOARD_SETS]
    if payload["metadata"].get("included_set_ids") != expected_ids:
        raise ValueError("Generated dashboard scope does not match DASHBOARD_SETS")
    visible_ids = {record["set_id"] for record in payload["records"]}
    visible_ids.update(record["set_id"] for record in payload["feature_group_records"])
    if not visible_ids <= DASHBOARD_SET_IDS:
        raise ValueError(f"Dashboard payload leaks excluded sets: {sorted(visible_ids - DASHBOARD_SET_IDS)}")

    rows = load_scoped_dataset_rows()
    counts = Counter(row["set_id"] for row in rows)
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    (OUTPUT_DIR / "assets").mkdir(parents=True)
    (OUTPUT_DIR / "public_data").mkdir()
    (OUTPUT_DIR / "licenses").mkdir()

    shutil.copy2(SOURCE_DIR / "assets" / "plotly.min.js", OUTPUT_DIR / "assets" / "plotly.min.js")
    public_payload = rewrite_normalized_paths(payload)
    (OUTPUT_DIR / "dashboard_data.json").write_text(
        json.dumps(public_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    index = (SOURCE_DIR / "index.html").read_text(encoding="utf-8")
    index = index.replace(
        "  <title>Analysis Icon Clustering Dashboard</title>",
        '  <meta name="dashboard-mode" content="public-static">\n'
        '  <link rel="icon" href="data:,">\n'
        "  <title>Analysis Icon Clustering Dashboard</title>",
        1,
    )
    public_note = '<div style="padding:8px 20px;background:#eef5ff;border-bottom:1px solid #cbd8eb;font:13px system-ui,sans-serif">Public thesis edition · five scoped datasets · <a href="study-selection.html">Select study icons</a> · <a href="credits.html">Data sources and licenses</a></div>'
    marker = "<main id=\"clusteringView\""
    if marker not in index:
        raise ValueError("Could not insert the public-edition notice")
    index = index.replace(marker, public_note + "\n  " + marker, 1)
    (OUTPUT_DIR / "index.html").write_text(index, encoding="utf-8")

    copied = 0
    for row in rows:
        source = ROOT / row["normalized_path"]
        if not source.is_file():
            raise FileNotFoundError(source)
        target = OUTPUT_DIR / row["normalized_path"].removeprefix("icon_data/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1

    write_study_selection_assets(rows)

    ai_archive = export_compatible_ai_runs({record["icon_id"] for record in payload["feature_group_records"]})
    (OUTPUT_DIR / "public_data" / "ai_clustering.json").write_text(
        json.dumps(ai_archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "credits.html").write_text(credits_html(counts), encoding="utf-8")
    for detail in SOURCE_DETAILS:
        if detail["license_file"]:
            shutil.copy2(detail["license_file"], OUTPUT_DIR / "licenses" / f"{detail['set_id']}.txt")

    (OUTPUT_DIR / "_headers").write_text(
        "/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/normalized_256/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/dashboard_data.json\n  Cache-Control: public, max-age=300\n"
        "/public_data/*\n  Cache-Control: public, max-age=300\n"
        "/study_selection_data.json\n  Cache-Control: public, max-age=300\n",
        encoding="utf-8",
    )
    files = [path for path in OUTPUT_DIR.rglob("*") if path.is_file()]
    manifest = {
        "deployment_mode": "static_dashboard_with_study_selection_api",
        "dashboard_sets": [{"set_id": set_id, "set_name": name, "image_count": counts[set_id]} for set_id, name in DASHBOARD_SETS],
        "normalized_image_count": copied,
        "compatible_saved_ai_runs": len(ai_archive["runs"]),
        "excluded_incompatible_ai_runs": ai_archive["excluded_incompatible_run_count"],
        "study_selection": {"selection_version": "five-sets-20-v1", "required_per_set": 20, "total_required": 100},
        "file_count_before_manifest": len(files),
        "bytes_before_manifest": sum(path.stat().st_size for path in files),
        "dashboard_data_sha256": hashlib.sha256((OUTPUT_DIR / "dashboard_data.json").read_bytes()).hexdigest(),
    }
    (OUTPUT_DIR / "deployment_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT_DIR.relative_to(ROOT)} with {copied} images and {len(ai_archive['runs'])} compatible AI runs")


if __name__ == "__main__":
    main()
