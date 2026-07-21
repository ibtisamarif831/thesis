import sys
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import extract_icon_features as features


def test_worker_exception_is_recorded_without_aborting_other_rows(monkeypatch):
    def fake_extract(row, extractors, foreground_threshold):
        if row["icon_id"] == "broken":
            raise ValueError("synthetic failure")
        return {"icon_id": row["icon_id"]}, None

    monkeypatch.setattr(features, "extract_row", fake_extract)
    results, failures = features.extract_rows(
        [{"icon_id": "good"}, {"icon_id": "broken"}],
        workers=2,
        foreground_threshold=245,
    )

    assert results == [{"icon_id": "good"}]
    assert failures == [{"icon_id": "broken", "error": "ValueError: synthetic failure"}]


def test_full_foreground_stroke_widths_remain_finite():
    mask = np.ones((32, 32), dtype=bool)

    distances = features.distance_transform(mask)
    stats = features.stroke_skeleton_stats(mask)

    assert distances.shape == mask.shape
    assert np.isfinite(distances).all()
    assert np.isfinite(stats["stroke_width_mean"])
    assert np.isfinite(stats["stroke_width_std"])
