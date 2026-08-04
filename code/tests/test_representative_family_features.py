from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard
from evaluation import build_feature_v2_benchmark as benchmark


EXPECTED_REPRESENTATIVES = {
    "complexity": "canny_edge_density",
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


def test_shape_representative_uses_plain_language_interpretation() -> None:
    shape = next(section for section in dashboard.image_feature_sections() if section["id"] == "shape")

    assert shape["representative_interpretation"] == (
        "Lower values usually mean a thin, open, or spread-out shape. "
        "Higher values usually mean a large, compact, or closed shape."
    )


def test_representative_preset_is_the_default_analysis_selection() -> None:
    assert dashboard.active_image_feature_columns() == list(EXPECTED_REPRESENTATIVES.values())


def test_feature_values_uses_exactly_the_feature_groups_representatives() -> None:
    assert dashboard.feature_explorer_representative_ids() == list(
        EXPECTED_REPRESENTATIVES.values()
    )


def test_complexity_benchmark_uses_current_representative() -> None:
    assert benchmark.FAMILIES["complexity"] == EXPECTED_REPRESENTATIVES["complexity"]


def test_feature_group_detail_uses_registry_label(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Selected feature Â· active registry" in index
    assert "Selected feature Â· schema v" not in index


def test_clustering_ui_tracks_current_family_representatives(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "state.activeFeatures = new Set(representativeFeatureIds());" in index
    assert "features: representativeFeature(section) ? [representativeFeature(section)] : []" in index
    assert "const ordered = representativeFeatureIds().filter" in index
    assert "const allowed = new Set(representativeFeatureIds());" in index
    assert "state.activeFeatures = new Set(featureIds.filter(featureId => allowed.has(featureId)));" in index
    assert "clusteringFeatureSections().forEach(section =>" in index
