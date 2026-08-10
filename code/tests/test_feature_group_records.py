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


def test_feature_group_payload_does_not_coerce_missing_values_to_zero() -> None:
    row = {
        "icon_id": "example",
        "label": "Example icon",
        "set_id": "set-a",
        "set_name": "Set A",
        "normalized_path": "icon_data/normalized_256/set-a/example.png",
    }
    for section in dashboard.image_feature_sections():
        row[section["representative_feature_id"]] = "0"
    row["mean_saturation_v2"] = "not-a-number"

    [record] = dashboard.build_feature_group_records([row])

    assert record["image_features"]["canny_edge_density"] == 0
    assert record["image_features"]["mean_saturation_v2"] is None


def test_feature_group_pilot_size_is_twenty() -> None:
    assert dashboard.FEATURE_GROUP_BIN_COUNT == 10
    assert dashboard.FEATURE_GROUP_SAMPLES_PER_BIN == 2
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
    assert "feature_group_bin_count || 10" in index
    assert "feature_group_samples_per_bin || 2" in index
    assert "familyComparisonIds.size < 3" in index
    assert 'aria-pressed="${isSelected}"' in index


def test_dashboard_exposes_only_configured_family_representatives(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'class="family-representative-select"' not in index
    assert "representativeFeaturesByFamily" not in index
    assert "updateRepresentativeFeature" not in index
    assert "state.activeFeatures = new Set(representativeFeatureIds());" in index
    assert "const selectedFeature = representativeFeature(section)" in index
    assert "const compareFeature = representativeFeature(compareSection)" in index
    assert "return dashboard.feature_group_records || []" in index
    assert "this session override is exploratory" not in index


def test_feature_group_html_uses_equal_width_stratified_sampling(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "drawEqualWidthStratifiedSample(population, featureId)" in index
    assert "feature_group_bin_count || 10" in index
    assert "feature_group_samples_per_bin || 2" in index
    assert "const width = (maximum - minimum) / binCount" in index
    assert "Math.min(binCount - 1" in index
    assert "randomSample(bin, samplesPerBin)" in index
    assert "Randomly sampled up to 2 per equal-width value bin" in index
    assert "Average of shown icons" in index


def test_all_feature_group_samples_are_shared_with_image_clustering(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "sharedSampleFamilyId = visibleFeatureSections()[0]?.id || null" in index
    assert "function setSharedClusteringSample(familyId, colorMode)" in index
    assert "function clusteringRecords()" in index
    assert "function combinedFamilySample(colorMode)" in index
    assert "return combinedFamilySample(sharedSampleColorMode)" in index
    assert "filter(record => !usedIconIds.has(record.icon_id))" in index
    assert "setSharedClusteringSample(activeFamilyId, familyColorMode)" in index
    assert "const records = clusteringRecords()" in index
    assert '`${records.length} shared icons · ${visibleFeatureSections().length} feature families' in index
    assert 'family_id: "all_families"' in index
    assert "records.map(record => record.icon_id).join" in index


def test_feature_group_html_preserves_meaningful_zero_and_flags_low_information(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "function representativeValue(record, featureId)" in index
    assert "function representativeValueProfile(population, featureId)" in index
    assert "function axialMeanDegrees(values)" in index
    assert "function axialOffsetDegrees(value, center)" in index
    assert "Valid zero and near-zero measurements remain included" in index
    assert "Low information in this cohort" in index
    assert "rather than treated as missing" in index


def test_orientation_gallery_excludes_undefined_records_before_sampling(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "function hasDefinedOrientation(record)" in index
    assert 'selectedFeature.id !== "principal_axis_orientation_v2"' in index
    assert "representativeRecordIsEligible(familyId, record)" in index
    assert "const population = familyPopulation(familyId, colorMode)" in index
    assert "only confidence-defined orientations are shown" in index
    assert "undefined orientations appear last" not in index
