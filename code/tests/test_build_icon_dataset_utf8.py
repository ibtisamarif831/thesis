import csv
import hashlib
import json
import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_icon_dataset as dataset


def test_metadata_and_dataset_io_are_utf8(tmp_path, monkeypatch):
    iconsets = tmp_path / "iconsets"
    arasaac = iconsets / "07_arasaac_pictograms" / "metadata"
    openmoji = iconsets / "10_openmoji" / "data"
    arasaac.mkdir(parents=True)
    openmoji.mkdir(parents=True)
    (arasaac / "arasaac_all_en.json").write_text(
        json.dumps([{"_id": 1, "keywords": [{"keyword": "niño"}], "categories": ["comunicación"]}], ensure_ascii=False),
        encoding="utf-8",
    )
    (openmoji / "openmoji.json").write_text(
        json.dumps([{"hexcode": "1F642", "annotation": "微笑 🙂", "group": "people", "subgroups": "face", "emoji": "🙂", "tags": "smile"}], ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(dataset, "ICONSETS_DIR", iconsets)

    assert dataset.load_arasaac_metadata()["1"]["label"] == "niño"
    assert dataset.load_openmoji_metadata()["1F642"]["label"] == "微笑 🙂"

    output = tmp_path / "dataset.csv"
    monkeypatch.setattr(dataset, "DATASET_CSV", output)
    row = {
        "icon_id": "id",
        "set_id": "set",
        "set_name": "OpenMoji",
        "relative_path": "source.svg",
        "filename": "source.svg",
        "label": "微笑 🙂",
        "category": "people",
        "format": "svg",
        "source": "source",
        "source_url": "https://example.test",
        "normalized_path": "normalized.png",
        "notes": "niño",
    }
    dataset.write_dataset([row])
    with output.open(newline="", encoding="utf-8") as handle:
        assert next(csv.DictReader(handle))["label"] == "微笑 🙂"


def test_normalized_path_identity_uses_posix_separators(tmp_path, monkeypatch):
    relative = Path("icon_data") / "iconsets" / "10_openmoji" / "color" / "svg" / "1F642.svg"
    monkeypatch.setattr(dataset, "NORMALIZED_DIR", tmp_path / "normalized_256")

    output = dataset.normalized_output_path(relative)
    expected_digest = hashlib.sha1(relative.as_posix().encode("utf-8")).hexdigest()[:12]

    assert output.name == f"1f642__{expected_digest}.png"
