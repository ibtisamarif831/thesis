from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard


EXPECTED_REPRESENTATIVES = {
    "complexity": "quadtree_structural_variability_v2",
    "shape": "enclosure_score_v2",
    "structure": "principal_axis_orientation_v2",
    "density_fill": "solid_fill_ratio_v2",
    "balance_layout": "horizontal_symmetry_v2",
    "color_contrast": "mean_saturation_v2",
    "texture": "local_texture_variation_v2",
}


def test_each_family_has_one_documented_representative_feature() -> None:
    sections = dashboard.image_feature_sections()

    assert {section["id"]: section["representative_feature_id"] for section in sections} == (
        EXPECTED_REPRESENTATIVES
    )
    for section in sections:
        representative = section["representative_feature"]
        assert representative["id"] == section["representative_feature_id"]
        assert representative["id"] in {feature["id"] for feature in section["features"]}
        assert section["representative_interpretation"]
        assert section["representative_rationale"]
        assert section["representative_evidence"]
        assert section["representative_citation"]


def test_representative_selection_does_not_shrink_active_feature_registry() -> None:
    assert len(dashboard.active_image_feature_columns()) == 81
