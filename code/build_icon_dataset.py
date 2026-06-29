#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICONSETS_DIR = ROOT / "icon_data/iconsets"
ANALYSIS_DIR = ROOT / "icon_data/analysis"
NORMALIZED_DIR = ROOT / "icon_data/normalized_256"
DATASET_CSV = ANALYSIS_DIR / "dataset.csv"

IMAGE_EXTENSIONS = {".svg", ".png", ".gif", ".jpg", ".jpeg"}

SET_INFO = {
    "01_mcdougall_symbol_icon_set": {
        "name": "McDougall Symbol/Icon Set",
        "source": "McDougall et al. BURO eprint",
        "source_url": "https://eprints.bournemouth.ac.uk/10165/",
    },
    "02_aiga_dot_symbol_signs": {
        "name": "AIGA/DOT Symbol Signs",
        "source": "AIGA/Wikimedia Commons",
        "source_url": "https://www.aiga.org/resources/symbol-signs",
    },
    "03_mapbox_maki_icons": {
        "name": "Mapbox Maki",
        "source": "Mapbox Maki GitHub",
        "source_url": "https://github.com/mapbox/maki",
    },
    "04_ocha_humanitarian_icons": {
        "name": "OCHA Humanitarian Icons",
        "source": "MapAction OCHA humanitarian icons for GIS",
        "source_url": "https://github.com/mapaction/ocha-humanitarian-icons-for-gis",
    },
    "05_mulberry_symbols": {
        "name": "Mulberry Symbols",
        "source": "Mulberry Symbols GitHub",
        "source_url": "https://github.com/mulberrysymbols/mulberry-symbols",
    },
    "06_blissymbolics": {
        "name": "Blissymbolics",
        "source": "Blissymbolics GitHub",
        "source_url": "https://github.com/blissymbolics/blissymbols",
    },
    "07_arasaac_pictograms": {
        "name": "ARASAAC Pictograms",
        "source": "ARASAAC API/static pictograms",
        "source_url": "https://arasaac.org",
    },
    "08_ghs_hazard_pictograms": {
        "name": "GHS Hazard Pictograms",
        "source": "OSHA Hazard Communication Pictograms",
        "source_url": "https://www.osha.gov/hazcom/pictograms",
    },
    "09_universal_symbols_healthcare_webfont": {
        "name": "Universal Symbols Healthcare Webfont",
        "source": "webfont-medical-icons GitHub",
        "source_url": "https://github.com/samcome/webfont-medical-icons",
    },
    "10_openmoji": {
        "name": "OpenMoji",
        "source": "OpenMoji GitHub",
        "source_url": "https://github.com/hfg-gmuend/openmoji",
    },
    "11_iso_7010_safety_signs": {
        "name": "ISO 7010 Safety Signs",
        "source": "ISO7010-Font GitHub",
        "source_url": "https://github.com/Adewra/ISO7010-Font",
    },
    "12_iso_15223_medical_device_symbols": {
        "name": "ISO 15223 Medical Device Symbols",
        "source": "medical-device-symbols GitHub",
        "source_url": "https://github.com/t4dhg/medical-device-symbols",
    },
    "13_usp_pictograms_manual": {
        "name": "USP Pictograms",
        "source": "USP Pictograms",
        "source_url": "https://www.usp.org/health-quality-safety/usp-pictograms",
    },
}


def slug_to_label(value: str) -> str:
    value = Path(value).stem
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def load_arasaac_metadata():
    path = ICONSETS_DIR / "07_arasaac_pictograms/metadata/arasaac_all_en.json"
    if not path.exists():
        return {}
    records = json.loads(path.read_text())
    out = {}
    for record in records:
        pictogram_id = str(record.get("_id", ""))
        keywords = record.get("keywords") or []
        label = ""
        if keywords:
            label = keywords[0].get("keyword") or ""
        categories = record.get("categories") or record.get("tags") or []
        out[pictogram_id] = {
            "label": label,
            "category": "; ".join(categories[:3]),
            "notes": f"arasaac_id={pictogram_id}",
        }
    return out


def load_openmoji_metadata():
    path = ICONSETS_DIR / "10_openmoji/data/openmoji.json"
    if not path.exists():
        return {}
    records = json.loads(path.read_text())
    out = {}
    for record in records:
        hexcode = record.get("hexcode", "")
        out[hexcode] = {
            "label": record.get("annotation", ""),
            "category": " / ".join(
                part for part in [record.get("group", ""), record.get("subgroups", "")] if part
            ),
            "notes": f"emoji={record.get('emoji', '')}; tags={record.get('tags', '')}",
        }
    return out


def load_mcdougall_metadata():
    path = ICONSETS_DIR / "01_mcdougall_symbol_icon_set/metadata/mcdougall_ratings.csv"
    if not path.exists():
        return {}
    with path.open(newline="") as file:
        records = csv.DictReader(file)
        return {
            row["appendix_item"]: {
                "label": row.get("label", ""),
                "notes": f"appendix_item={row['appendix_item']}",
            }
            for row in records
            if row.get("appendix_item")
        }


def infer_category(set_id: str, relative_parts: tuple[str, ...]) -> str:
    if set_id == "03_mapbox_maki_icons":
        return "cartography / point of interest"
    if set_id == "04_ocha_humanitarian_icons":
        return relative_parts[1].removeprefix("humanitarian-icons-v2-1-") if len(relative_parts) > 1 else ""
    if set_id == "05_mulberry_symbols":
        return relative_parts[1] if len(relative_parts) > 1 else "AAC"
    if set_id == "06_blissymbolics":
        return "Blissymbolics " + relative_parts[4].removesuffix("s") if len(relative_parts) > 4 else "Blissymbolics"
    if set_id == "08_ghs_hazard_pictograms":
        return "chemical hazard"
    if set_id == "09_universal_symbols_healthcare_webfont":
        return "healthcare wayfinding"
    if set_id == "11_iso_7010_safety_signs":
        return relative_parts[1] if len(relative_parts) > 1 else "safety sign"
    if set_id == "12_iso_15223_medical_device_symbols":
        return "medical device label"
    if set_id == "13_usp_pictograms_manual":
        return "medication instruction"
    return ""


def is_canonical_icon(path: Path, set_id: str) -> bool:
    parts = path.relative_to(ICONSETS_DIR / set_id).parts
    rel = "/".join(parts)

    if set_id == "01_mcdougall_symbol_icon_set":
        return rel.startswith("extracted_icons_png/") and path.suffix.lower() == ".png"
    if set_id == "02_aiga_dot_symbol_signs":
        return rel.startswith("png_512/") and path.suffix.lower() == ".png"
    if set_id == "03_mapbox_maki_icons":
        return rel.startswith("icons/") and path.suffix.lower() == ".svg"
    if set_id == "04_ocha_humanitarian_icons":
        return rel.startswith("humanitarian-icons-v2-1-svg/") and path.suffix.lower() == ".svg"
    if set_id == "05_mulberry_symbols":
        return rel.startswith("EN/") and path.suffix.lower() == ".svg"
    if set_id == "06_blissymbolics":
        return (
            (rel.startswith("rendered_svg/chars/") or rel.startswith("rendered_svg/words/"))
            and path.suffix.lower() == ".svg"
        )
    if set_id == "07_arasaac_pictograms":
        return rel.startswith("png_300/") and path.suffix.lower() == ".png"
    if set_id == "08_ghs_hazard_pictograms":
        return rel.startswith("png_osha/") and path.suffix.lower() == ".png"
    if set_id == "09_universal_symbols_healthcare_webfont":
        return rel.startswith("packages/svg/") and path.suffix.lower() == ".svg"
    if set_id == "10_openmoji":
        return rel.startswith("color/svg/") and path.suffix.lower() == ".svg"
    if set_id == "11_iso_7010_safety_signs":
        return "Warning Symbols/" in rel and path.suffix.lower() == ".svg" and "_Original" not in path.stem
    if set_id == "12_iso_15223_medical_device_symbols":
        return rel.startswith("src/icons/") and path.suffix.lower() == ".svg"
    if set_id == "13_usp_pictograms_manual":
        return rel.startswith("gif/pictogif/") and path.suffix.lower() == ".gif"
    return False


def normalized_output_path(relative_path: Path) -> Path:
    digest = hashlib.sha1(str(relative_path).encode("utf-8")).hexdigest()[:12]
    set_id = relative_path.parts[2]
    stem = slug_to_label(relative_path.name).lower().replace(" ", "_")[:80] or "icon"
    return NORMALIZED_DIR / set_id / f"{stem}__{digest}.png"


def build_rows():
    arasaac_meta = load_arasaac_metadata()
    openmoji_meta = load_openmoji_metadata()
    mcdougall_meta = load_mcdougall_metadata()
    rows = []

    for path in sorted(ICONSETS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        relative_path = path.relative_to(ROOT)
        parts = relative_path.parts
        if len(parts) < 3:
            continue
        set_id = parts[2]
        if set_id not in SET_INFO:
            continue
        if not is_canonical_icon(path, set_id):
            continue

        label = slug_to_label(path.name)
        category = infer_category(set_id, parts)
        notes = ""

        if set_id == "07_arasaac_pictograms":
            item = arasaac_meta.get(path.stem, {})
            label = item.get("label") or label
            category = item.get("category") or category
            notes = item.get("notes", "")
        elif set_id == "10_openmoji":
            item = openmoji_meta.get(path.stem, {})
            label = item.get("label") or label
            category = item.get("category") or category
            notes = item.get("notes", "")
        elif set_id == "01_mcdougall_symbol_icon_set":
            match = re.search(r"mcdougall_(\d+)", path.stem)
            if match:
                appendix_item = str(int(match.group(1)))
                item = mcdougall_meta.get(appendix_item, {})
                label = item.get("label") or f"McDougall item {appendix_item}"
                notes = item.get("notes", f"appendix_item={appendix_item}")
        elif set_id == "06_blissymbolics":
            label = re.sub(r"__[0-9a-f]{12}$", "", path.stem)
            label = slug_to_label(label)
            kind = "char" if parts[4] == "chars" else "word"
            notes = f"bliss_kind={kind}"

        info = SET_INFO[set_id]
        normalized = normalized_output_path(relative_path)
        rows.append(
            {
                "icon_id": hashlib.sha1(str(relative_path).encode("utf-8")).hexdigest()[:16],
                "set_id": set_id,
                "set_name": info["name"],
                "relative_path": str(relative_path),
                "filename": path.name,
                "label": label,
                "category": category,
                "format": path.suffix.lower().lstrip("."),
                "source": info["source"],
                "source_url": info["source_url"],
                "normalized_path": str(normalized.relative_to(ROOT)),
                "notes": notes,
            }
        )

    return rows


def write_dataset(rows):
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "icon_id",
        "set_id",
        "set_name",
        "relative_path",
        "filename",
        "label",
        "category",
        "format",
        "source",
        "source_url",
        "normalized_path",
        "notes",
    ]
    with DATASET_CSV.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_one(row, force=False):
    source = ROOT / row["relative_path"]
    dest = ROOT / row["normalized_path"]
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return True, row["relative_path"], "exists"

    dest.parent.mkdir(parents=True, exist_ok=True)
    input_path = str(source)
    if source.suffix.lower() == ".gif":
        input_path += "[0]"

    command = [
        "magick",
        input_path,
        "-auto-orient",
        "-resize",
        "256x256",
        "-background",
        "none",
        "-gravity",
        "center",
        "-extent",
        "256x256",
        str(dest),
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        return False, row["relative_path"], result.stderr.strip()
    return True, row["relative_path"], "normalized"


def normalize(rows, workers, limit=None, force=False):
    selected = rows[:limit] if limit else rows
    failures = []
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(normalize_one, row, force) for row in selected]
        for future in as_completed(futures):
            ok, source, message = future.result()
            completed += 1
            if not ok:
                failures.append({"relative_path": source, "error": message})
            if completed % 1000 == 0:
                print(f"Normalized/checked {completed}/{len(selected)}")

    failure_path = ANALYSIS_DIR / "normalization_failures.json"
    failure_path.write_text(json.dumps(failures, indent=2))
    print(f"Normalization target rows: {len(selected)}")
    print(f"Normalization failures: {len(failures)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    write_dataset(rows)
    print(f"Wrote {len(rows)} rows to {DATASET_CSV}")

    if args.normalize:
        normalize(rows, workers=args.workers, limit=args.limit, force=args.force)


if __name__ == "__main__":
    main()
