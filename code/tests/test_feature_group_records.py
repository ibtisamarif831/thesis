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


def test_feature_group_payload_excludes_uncertain_masks() -> None:
    certain = {
        "icon_id": "certain",
        "label": "Certain icon",
        "set_id": "set-a",
        "set_name": "Set A",
        "normalized_path": "icon_data/normalized_256/set-a/certain.png",
        "mask_is_uncertain": "false",
    }
    uncertain = {
        **certain,
        "icon_id": "uncertain",
        "normalized_path": "icon_data/normalized_256/set-a/uncertain.png",
        "mask_is_uncertain": "true",
    }
    for section in dashboard.image_feature_sections():
        certain[section["representative_feature_id"]] = "0.25"
        uncertain[section["representative_feature_id"]] = "0.75"

    records = dashboard.build_feature_group_records([certain, uncertain])

    assert [record["icon_id"] for record in records] == ["certain"]
    assert records[0]["mask_is_uncertain"] is False


def test_feature_group_pilot_size_is_twenty() -> None:
    assert dashboard.FEATURE_GROUP_SAMPLE_SIZE == 20


def test_feature_group_comparison_size_is_three() -> None:
    assert dashboard.FEATURE_GROUP_COMPARISON_SIZE == 3


def test_feature_group_html_supports_three_icon_comparison(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Pick 3 icons to compare" in index
    assert 'id="comparisonModal"' in index
    assert 'class="comparison-dialog"' in index
    assert ".comparison-dialog { width: 100vw; height: 100vh; height: 100dvh;" in index
    assert "View fullscreen comparison" in index
    assert "openFamilyComparison(nextButton)" in index
    assert "feature_group_sample_size || 20" in index
    assert "familyComparisonIds.size < 3" in index
    assert 'aria-pressed="${isSelected}"' in index


def test_representative_change_updates_clustering_without_reload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'class="family-representative-select"' in index
    assert 'select.addEventListener("change"' in index
    assert "representativeFeaturesByFamily.set(familyId, featureId)" in index
    assert "setActiveFeatures(representativeFeatureIds())" in index
    assert "computedCache.clear()" in index
    assert "familySamples.delete(key)" in index
    assert "const selectedFeature = representativeFeature(section)" in index
    assert "const compareFeature = representativeFeature(compareSection)" in index
    assert "return dashboard.records || []" in index
    assert "this session override is exploratory" in index


def test_feature_group_html_uses_dataset_balanced_sampling(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "drawDatasetBalancedSample(population, limit, key)" in index
    assert "datasetDrawCounts: new Map()" in index
    assert 'const dataset = record.set_name || "Unknown dataset"' in index
    assert "dataset-balanced icons from" in index
    assert "Average of shown icons" in index
