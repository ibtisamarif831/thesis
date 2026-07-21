from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard


def test_feature_group_payload_keeps_only_pilot_fields() -> None:
    row = {
        "icon_id": "example",
        "label": "Example icon",
        "set_id": "set-a",
        "set_name": "Set A",
        "normalized_path": "icon_data/normalized_256/set-a/example.png",
        "is_monochrome": "1",
        "unused_feature": "999",
    }
    for section in dashboard.image_feature_sections():
        row[section["representative_feature_id"]] = "0.25"

    records = dashboard.build_feature_group_records([row])

    assert len(records) == 1
    assert records[0]["icon_id"] == "example"
    assert records[0]["normalized_path"].endswith("normalized_256/set-a/example.png")
    assert set(records[0]["image_features"]) == {
        "is_monochrome",
        "orientation_confidence_v2",
        "red_pixel_ratio_v2",
        "strict_red_flag_v2",
        *(section["representative_feature_id"] for section in dashboard.image_feature_sections()),
    }
    assert "unused_feature" not in records[0]["image_features"]


def test_feature_group_pilot_size_is_twenty() -> None:
    assert dashboard.FEATURE_GROUP_SAMPLE_SIZE == 20
