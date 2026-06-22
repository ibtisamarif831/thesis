#!/usr/bin/env python3
import argparse
import csv
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "icon_data/iconsets/01_mcdougall_symbol_icon_set/appendix_pages_png"
METADATA_DIR = ROOT / "icon_data/iconsets/01_mcdougall_symbol_icon_set/metadata"
OUTPUT_CSV = METADATA_DIR / "mcdougall_ratings.csv"
REVIEW_CSV = METADATA_DIR / "mcdougall_ratings_review.csv"

ROW_TOPS = [320, 660, 1000, 1340, 1710]
VALUE_OFFSETS = [8, 42, 76, 110, 144, 178, 212, 246]

FIELDS = [
    "concreteness",
    "complexity",
    "familiarity",
    "meaningfulness",
    "semantic_distance",
    "complexity_metric",
    "concept_agreement",
    "name_agreement",
]

# Corrections for source-visible OCR failures that are not recoverable from
# alternate Tesseract page segmentation modes.
OCR_CORRECTIONS = {
    (1, "semantic_distance"): "2.03",
    (2, "familiarity"): "1.93",
    (160, "name_agreement"): "15.00",
    (181, "complexity"): "2.53",
    (181, "complexity_metric"): "25",
    (194, "concreteness"): "2.12",
    (199, "concreteness"): "4.62",
    (199, "complexity"): "2.58",
    (199, "familiarity"): "3.65",
    (199, "meaningfulness"): "3.75",
    (199, "semantic_distance"): "2.43",
    (199, "complexity_metric"): "4",
    (199, "concept_agreement"): "0.00",
    (199, "name_agreement"): "70.00",
    (200, "concreteness"): "2.20",
    (200, "complexity"): "2.85",
    (200, "familiarity"): "2.28",
    (200, "meaningfulness"): "1.88",
    (200, "semantic_distance"): "1.79",
    (200, "complexity_metric"): "10",
    (200, "concept_agreement"): "0.00",
    (200, "name_agreement"): "20.00",
    (226, "concept_agreement"): "2.50",
    (226, "name_agreement"): "27.50",
    (227, "concreteness"): "2.80",
    (227, "complexity"): "1.55",
    (227, "familiarity"): "2.45",
    (227, "meaningfulness"): "2.55",
    (227, "semantic_distance"): "2.12",
    (227, "complexity_metric"): "1",
    (227, "concept_agreement"): "0.00",
    (227, "name_agreement"): "62.50",
    (228, "concreteness"): "2.02",
    (228, "complexity"): "2.40",
    (228, "familiarity"): "1.80",
    (228, "meaningfulness"): "1.57",
    (228, "semantic_distance"): "2.76",
    (228, "complexity_metric"): "7",
    (228, "concept_agreement"): "5.00",
    (228, "name_agreement"): "7.50",
    (229, "concreteness"): "4.83",
    (229, "complexity"): "3.28",
    (229, "familiarity"): "3.90",
    (229, "meaningfulness"): "3.92",
    (229, "semantic_distance"): "4.69",
    (229, "complexity_metric"): "9",
    (229, "concept_agreement"): "57.50",
    (229, "name_agreement"): "57.50",
    (230, "concreteness"): "3.95",
    (230, "complexity"): "2.78",
    (230, "familiarity"): "3.00",
    (230, "meaningfulness"): "3.13",
    (230, "semantic_distance"): "4.40",
    (230, "complexity_metric"): "12",
    (230, "concept_agreement"): "60.00",
    (230, "name_agreement"): "60.00",
}

LABEL_CORRECTIONS = {
    5: "Air vent - right and left outlets",
    199: "Search",
    200: "Select irregular area",
    227: "Vertebrates",
    228: "Vibrate",
    229: "Video camera",
    230: "Wall",
}

COMMON_RESPONSE_CORRECTIONS = {
    199: "torch",
    200: "star",
    227: "bone",
    228: "expanding",
}

OUTPUT_FIELDNAMES = [
    "appendix_item",
    "label",
    *FIELDS,
    "common_response",
    "source_page",
    "ocr_confidence",
    "verified",
]

REVIEW_FIELDNAMES = [
    "appendix_item",
    "source_page",
    "field",
    "value",
    "confidence",
    "reason",
]

NUMERIC_RE = re.compile(r"^[0-9][0-9.]*$")


def main():
    parser = argparse.ArgumentParser(description="Extract McDougall appendix ratings metadata with OCR.")
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--review-output", type=Path, default=REVIEW_CSV)
    parser.add_argument("--no-fallback", action="store_true", help="Disable targeted OCR fallback crops.")
    args = parser.parse_args()

    tesseract = shutil.which("tesseract")
    if not tesseract:
        raise SystemExit("tesseract was not found on PATH")

    rows, review_rows = extract_rows(tesseract, fallback=not args.no_fallback)
    validate_rows(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with args.review_output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"Wrote {len(review_rows)} review rows to {args.review_output}")


def extract_rows(tesseract: str, fallback: bool):
    rows = []
    review_rows = []
    item = 1

    for page_number in range(9, 32):
        words = ocr_page_words(tesseract, SOURCE_DIR / f"mcdougall_appendix_page-{page_number:02d}.png")
        image = Image.open(SOURCE_DIR / f"mcdougall_appendix_page-{page_number:02d}.png").convert("L")
        for row_index in range(5):
            for side in ("left", "right"):
                row, reviews = extract_item(
                    tesseract=tesseract,
                    image=image,
                    words=words,
                    appendix_item=item,
                    source_page=page_number,
                    row_index=row_index,
                    side=side,
                    fallback=fallback,
                )
                rows.append(row)
                review_rows.extend(reviews)
                item += 1

    page_number = 32
    words = ocr_page_words(tesseract, SOURCE_DIR / f"mcdougall_appendix_page-{page_number:02d}.png")
    image = Image.open(SOURCE_DIR / f"mcdougall_appendix_page-{page_number:02d}.png").convert("L")
    for row_index, side in [(0, "left"), (0, "right"), (1, "left"), (1, "right"), (2, "left"), (2, "right"), (3, "left"), (3, "right"), (4, "left")]:
        row, reviews = extract_item(
            tesseract=tesseract,
            image=image,
            words=words,
            appendix_item=item,
            source_page=page_number,
            row_index=row_index,
            side=side,
            fallback=fallback,
        )
        rows.append(row)
        review_rows.extend(reviews)
        item += 1

    return rows, review_rows


def ocr_page_words(tesseract: str, image_path: Path):
    command = [tesseract, str(image_path), "stdout", "--psm", "6", "tsv"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Tesseract failed for {image_path}: {result.stderr.strip()}")

    lines = result.stdout.splitlines()
    if not lines:
        return []

    reader = csv.DictReader(lines, delimiter="\t")
    words = []
    for row in reader:
        text = (row.get("text") or "").strip()
        if row.get("level") != "5" or not text:
            continue
        try:
            left = int(float(row["left"]))
            top = int(float(row["top"]))
            width = int(float(row["width"]))
            height = int(float(row["height"]))
            confidence = float(row["conf"])
        except (KeyError, ValueError):
            continue
        words.append(
            {
                "text": text,
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "right": left + width,
                "bottom": top + height,
                "cx": left + width / 2,
                "cy": top + height / 2,
                "confidence": confidence,
            }
        )
    return words


def extract_item(tesseract, image, words, appendix_item, source_page, row_index, side, fallback):
    top = ROW_TOPS[row_index]
    geometry = item_geometry(top, side)
    reviews = []

    label_words = words_in_box(words, geometry["label_box"])
    label = clean_label(label_words)
    label = LABEL_CORRECTIONS.get(appendix_item, label)
    expected_token = str(appendix_item)
    if not label_words or not any(w["text"].strip().lstrip("GQO") == expected_token for w in label_words[:2]):
        reviews.append(review(appendix_item, source_page, "label", label, mean_confidence(label_words), "item_number_not_confirmed"))
    if not label:
        reviews.append(review(appendix_item, source_page, "label", label, mean_confidence(label_words), "missing_label"))

    row = {
        "appendix_item": appendix_item,
        "label": label,
        "common_response": "",
        "source_page": source_page,
        "ocr_confidence": "",
        "verified": "false",
    }
    confidences = []

    for field, offset in zip(FIELDS, VALUE_OFFSETS):
        value_box = field_value_box(words, geometry, top, field, offset)
        value, confidence, raw_text = extract_numeric_from_words(words, value_box, field)
        reason = review_reason_for_numeric(field, value, confidence)

        if fallback and reason:
            fallback_value, fallback_confidence, fallback_raw = ocr_numeric_crop(
                tesseract,
                image.crop(value_box),
                field,
            )
            fallback_reason = review_reason_for_numeric(field, fallback_value, fallback_confidence)
            if should_use_fallback(reason, fallback_reason, confidence, fallback_confidence):
                if value != fallback_value:
                    reviews.append(
                        review(
                            appendix_item,
                            source_page,
                            field,
                            f"{value} -> {fallback_value}",
                            fallback_confidence,
                            f"fallback_from:{raw_text or 'blank'}",
                        )
                    )
                value = fallback_value
                confidence = fallback_confidence
                reason = fallback_reason
                raw_text = fallback_raw

        correction = OCR_CORRECTIONS.get((appendix_item, field))
        if correction and value != correction:
            reviews.append(
                review(
                    appendix_item,
                    source_page,
                    field,
                    f"{value or raw_text} -> {correction}",
                    confidence,
                    "explicit_ocr_correction",
                )
            )
            value = correction
            reason = review_reason_for_numeric(field, value, confidence)

        row[field] = value
        confidences.append(confidence)
        if reason:
            reviews.append(review(appendix_item, source_page, field, value or raw_text, confidence, reason))

    common_words = words_in_box(words, geometry["common_box"])
    common_response = clean_common_response(common_words)
    common_response = COMMON_RESPONSE_CORRECTIONS.get(appendix_item, common_response)
    row["common_response"] = common_response
    if not common_response:
        reviews.append(review(appendix_item, source_page, "common_response", "", mean_confidence(common_words), "missing_common_response"))
    else:
        confidences.append(mean_confidence([w for w in common_words if w["text"] in common_response.split()]))

    row["ocr_confidence"] = f"{mean_values(confidences):.2f}" if confidences else ""
    return row, reviews


def item_geometry(top, side):
    if side == "left":
        return {
            "label_box": (200, top, 485, top + 115),
            "metric_label_box": (480, top, 700, top + 300),
            "value_x": (700, 800),
            "common_box": (570, top + 255, 800, top + 335),
        }
    return {
        "label_box": (890, top, 1165, top + 115),
        "metric_label_box": (1135, top, 1360, top + 300),
        "value_x": (1360, 1475),
        "common_box": (1230, top + 255, 1475, top + 335),
    }


def words_in_box(words, box):
    x1, y1, x2, y2 = box
    return [
        word
        for word in words
        if x1 <= word["cx"] <= x2 and y1 <= word["cy"] <= y2
    ]


def clean_label(words):
    kept = []
    for word in ordered_text_words(words):
        text = normalize_text(word["text"])
        lower = text.lower().rstrip(":")
        if not text or lower in {"concreteness", "complexity", "familiarity"}:
            continue
        if re.fullmatch(r"\d+", text):
            continue
        text = re.sub(r"^[A-Za-z]*\d+", "", text).strip()
        if not text:
            continue
        kept.append(text)
    label = " ".join(kept)
    label = re.sub(r"\s+", " ", label).strip()
    return label


def ordered_text_words(words, line_tolerance=24):
    lines = []
    for word in sorted(words, key=lambda item: item["cy"]):
        for line in lines:
            if abs(mean_values([item["cy"] for item in line]) - word["cy"]) <= line_tolerance:
                line.append(word)
                break
        else:
            lines.append([word])
    ordered = []
    for line in sorted(lines, key=lambda items: mean_values([item["cy"] for item in items])):
        ordered.extend(sorted(line, key=lambda item: item["left"]))
    return ordered


def extract_numeric_from_words(words, box, field):
    candidates = []
    for word in words_in_box(words, box):
        value = normalize_number(word["text"], field)
        if value:
            candidates.append((value, word["confidence"], word["text"]))
    if not candidates:
        return "", 0.0, ""
    return max(candidates, key=lambda item: item[1])


def field_value_box(words, geometry, top, field, offset):
    label_word = find_field_label_word(words, geometry["metric_label_box"], field)
    if label_word:
        return (
            geometry["value_x"][0],
            max(0, label_word["top"] - 6),
            geometry["value_x"][1],
            label_word["bottom"] + 12,
        )
    return (
        geometry["value_x"][0],
        top + offset,
        geometry["value_x"][1],
        top + offset + 44,
    )


def find_field_label_word(words, metric_label_box, field):
    candidates = words_in_box(words, metric_label_box)
    for word in sorted(candidates, key=lambda item: (item["top"], item["left"])):
        text = normalize_text(word["text"]).lower().rstrip(":")
        if field == "concreteness" and text.startswith("concreteness"):
            return word
        if field == "complexity" and (text == "complexity" or text.startswith("complext")):
            if not has_word_nearby(candidates, word, "metric"):
                return word
        if field == "familiarity" and text.startswith("familiarity"):
            return word
        if field == "meaningfulness" and text.startswith("meaningfulness"):
            return word
        if field == "semantic_distance" and text.startswith("semantic"):
            return word
        if field == "complexity_metric" and text.startswith("metric"):
            return word
        if field == "concept_agreement" and text.startswith("concept"):
            return word
        if field == "name_agreement" and text.startswith("name"):
            return word
    return None


def has_word_nearby(words, anchor, target):
    for word in words:
        if abs(word["cy"] - anchor["cy"]) > 15:
            continue
        text = normalize_text(word["text"]).lower().rstrip(":")
        if text.startswith(target):
            return True
    return False


def ocr_numeric_crop(tesseract, crop, field):
    scale = 5 if field in {"concept_agreement", "name_agreement"} else 4
    prepared = ImageOps.autocontrast(crop.convert("L")).resize((crop.width * scale, crop.height * scale))
    with tempfile.NamedTemporaryFile(suffix=".png") as temp:
        prepared.save(temp.name)
        command = [
            tesseract,
            temp.name,
            "stdout",
            "--psm",
            "7",
            "-c",
            "tessedit_char_whitelist=0123456789.",
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    raw_text = result.stdout.strip()
    value = normalize_number(raw_text, field)
    confidence = 70.0 if value else 0.0
    return value, confidence, raw_text


def normalize_text(value):
    value = re.sub(r"[^A-Za-z0-9 /&().'-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_number(value, field):
    value = re.sub(r"[^0-9.]", "", value)
    if not value:
        return ""
    if value.count(".") > 1:
        parts = value.split(".")
        value = parts[0] + "." + "".join(parts[1:])
    if field == "complexity_metric":
        digits = re.sub(r"\D", "", value)
        return str(int(digits)) if digits else ""
    if field not in {"complexity_metric", "concept_agreement", "name_agreement"} and "." not in value and len(value) == 2:
        value = value[0] + "." + value[1] + "0"
    elif "." not in value and len(value) == 3:
        value = value[0] + "." + value[1:]
    elif "." not in value and len(value) == 4 and field in {"concept_agreement", "name_agreement"}:
        value = value[:2] + "." + value[2:]
    try:
        number = float(value)
    except ValueError:
        return ""
    if field in {"concept_agreement", "name_agreement"} and number > 100:
        digits = re.sub(r"\D", "", value)
        if len(digits) == 3:
            value = digits[:2] + "." + digits[2] + "0"
        elif len(digits) == 4:
            value = digits[:2] + "." + digits[2:]
        try:
            number = float(value)
        except ValueError:
            return ""
    return f"{number:.2f}"


def review_reason_for_numeric(field, value, confidence):
    if not value:
        return "missing_numeric"
    try:
        number = float(value)
    except ValueError:
        return "invalid_numeric"
    if field == "complexity_metric":
        if not 0 <= number <= 100:
            return "complexity_metric_out_of_range"
        if confidence < 70:
            return "low_confidence"
        return ""
    if field in {"concept_agreement", "name_agreement"}:
        if not 0 <= number <= 100:
            return "agreement_out_of_range"
        if confidence < 80:
            return "low_confidence"
        return ""
    if not 1 <= number <= 5:
        return "rating_out_of_range"
    if confidence < 85:
        return "low_confidence"
    return ""


def should_use_fallback(reason, fallback_reason, confidence, fallback_confidence):
    if reason and reason != "low_confidence" and fallback_reason in {"", "low_confidence"}:
        return True
    if reason and not fallback_reason:
        return True
    if fallback_reason and not reason:
        return False
    return fallback_confidence > confidence + 10


def clean_common_response(words):
    candidates = []
    for word in sorted(words, key=lambda item: (item["top"], item["left"])):
        text = normalize_text(word["text"])
        lower = text.lower().rstrip(":")
        if not text:
            continue
        if lower in {"agreement", "name", "concept"} or "agreement" in lower:
            continue
        if NUMERIC_RE.match(text):
            continue
        candidates.append(text)
    return re.sub(r"\s+", " ", " ".join(candidates)).strip()


def mean_confidence(words):
    values = [word["confidence"] for word in words if word["confidence"] >= 0]
    return mean_values(values)


def mean_values(values):
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else 0.0


def review(appendix_item, source_page, field, value, confidence, reason):
    return {
        "appendix_item": appendix_item,
        "source_page": source_page,
        "field": field,
        "value": value,
        "confidence": f"{confidence:.2f}" if isinstance(confidence, (int, float)) else confidence,
        "reason": reason,
    }


def validate_rows(rows):
    if len(rows) != 239:
        raise SystemExit(f"Expected 239 rows, got {len(rows)}")

    item_numbers = [int(row["appendix_item"]) for row in rows]
    expected = list(range(1, 240))
    if item_numbers != expected:
        raise SystemExit("Appendix item numbers are not exactly 1..239")

    for row in rows:
        for field in FIELDS:
            reason = review_reason_for_numeric(field, row[field], 100.0)
            if reason and reason != "low_confidence":
                raise SystemExit(
                    f"Invalid {field} for appendix item {row['appendix_item']}: {row[field]} ({reason})"
                )


if __name__ == "__main__":
    main()
