from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard


def test_dashboard_scope_keeps_only_selected_human_study_sets() -> None:
    rows = [
        {"set_id": "02_aiga_dot_symbol_signs", "icon_id": "keep-aiga"},
        {"set_id": "04_ocha_humanitarian_icons", "icon_id": "keep-ocha"},
        {
            "set_id": "09_universal_symbols_healthcare_webfont",
            "icon_id": "keep-healthcare",
        },
        {"set_id": "11_iso_7010_safety_signs", "icon_id": "keep-safety"},
        {
            "set_id": "12_iso_15223_medical_device_symbols",
            "icon_id": "keep-medical",
        },
        {"set_id": "07_arasaac_pictograms", "icon_id": "exclude-arasaac"},
    ]

    filtered = dashboard.filter_dashboard_sets(rows)

    assert [row["icon_id"] for row in filtered] == [
        "keep-aiga",
        "keep-ocha",
        "keep-healthcare",
        "keep-safety",
        "keep-medical",
    ]
    assert dashboard.DASHBOARD_SET_IDS == {
        "02_aiga_dot_symbol_signs",
        "04_ocha_humanitarian_icons",
        "09_universal_symbols_healthcare_webfont",
        "11_iso_7010_safety_signs",
        "12_iso_15223_medical_device_symbols",
    }


def test_complete_feature_views_filter_the_canonical_feature_corpus(
    tmp_path, monkeypatch
) -> None:
    feature_path = tmp_path / "features.csv"
    feature_path.write_text(
        "set_id,icon_id,canny_edge_density\n"
        "02_aiga_dot_symbol_signs,keep,0.1\n"
        "07_arasaac_pictograms,exclude,0.2\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(dashboard, "ROOT", tmp_path)
    monkeypatch.setattr(dashboard, "FEATURES_PATH", feature_path)
    monkeypatch.setattr(dashboard, "IMAGE_FEATURE_COLUMNS", ["canny_edge_density"])

    review_rows, _ = dashboard.feature_review_source_rows({})
    explorer_rows, _ = dashboard.feature_explorer_source_rows([], {})

    assert [row["icon_id"] for row in review_rows] == ["keep"]
    assert [row["icon_id"] for row in explorer_rows] == ["keep"]


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


def test_feature_group_payload_excludes_missing_representative_values() -> None:
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

    records, audit = dashboard.build_feature_group_payload([row])

    assert records == []
    assert audit["excluded_row_count"] == 1
    assert audit["exclusion_reason_counts"] == {
        "missing_or_nonfinite_representative_value": 1
    }


def test_feature_group_quality_audit_keeps_valid_zero_and_low_tail_values() -> None:
    row = {
        "icon_id": "valid-low",
        "label": "Valid low icon",
        "set_id": "set-a",
        "set_name": "Set A",
        "normalized_path": "icon_data/normalized_256/set-a/valid-low.png",
        "mask_coverage": "0.001",
        "orientation_confidence_v2": "0.8",
    }
    for section in dashboard.image_feature_sections():
        row[section["representative_feature_id"]] = "0"

    records, audit = dashboard.build_feature_group_payload([row])

    assert [record["icon_id"] for record in records] == ["valid-low"]
    assert records[0]["image_features"]["mean_saturation_v2"] == 0
    assert records[0]["image_features"]["principal_axis_orientation_v2"] == 0
    assert audit["excluded_row_count"] == 0
    assert audit["low_tail_review"]["candidate_count"] == 1
    assert audit["low_tail_review"]["excluded_by_low_value_count"] == 0


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
    assert "function requiredRepresentativeValue(record, featureId)" in index
    assert "record.image_features[feature] || 0" not in index
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
