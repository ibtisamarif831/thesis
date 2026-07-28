from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


CODE_DIR = Path(__file__).resolve().parents[1]
ROOT = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard
import compute_icon_similarity as similarity
import extract_icon_features
from evaluation import build_feature_v2_benchmark as benchmark
from thesis_pipeline.features import registry


FIXTURE = Path(__file__).parent / "fixtures" / "feature_registry_v2.json"
DASHBOARD_PAYLOAD = ROOT / "icon_data/analysis/analysis_dashboard/dashboard_data.json"


def registry_snapshot() -> dict[str, object]:
    feature_evidence = {
        spec.id: {
            "evidence": spec.evidence,
            "citation": spec.citation,
        }
        for spec in registry.FEATURE_SPECS
        if spec.status is registry.FeatureStatus.ACTIVE
    }
    return {
        "feature_schema_version": registry.FEATURE_SCHEMA_VERSION,
        "orientation_confidence_threshold": registry.ORIENTATION_CONFIDENCE_THRESHOLD,
        "analysis_feature_preset": registry.ANALYSIS_FEATURE_PRESET,
        "analysis_feature_ids": list(registry.analysis_feature_ids()),
        "raw_feature_ids": list(registry.raw_feature_ids()),
        "active_feature_ids": list(registry.active_feature_ids()),
        "excluded_feature_ids": list(registry.excluded_feature_ids()),
        "representative_feature_ids": list(registry.representative_feature_ids()),
        "benchmark_family_features": dict(registry.benchmark_family_features()),
        "feature_statuses": {
            spec.id: spec.status.value for spec in registry.FEATURE_SPECS
        },
        "feature_evidence_scopes": {
            spec.id: spec.evidence_scope.value
            for spec in registry.FEATURE_SPECS
            if spec.status is registry.FeatureStatus.ACTIVE
        },
        "feature_evidence_sha256": hashlib.sha256(
            json.dumps(feature_evidence, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "families": [
            {
                "id": family.id,
                "title": family.title,
                "feature_ids": list(family.feature_ids),
                "representative_feature_id": family.representative_feature_id,
                "benchmark_family_id": family.benchmark_family_id,
            }
            for family in registry.family_specs()
        ],
        "excluded_feature_reasons": dict(registry.excluded_feature_reasons()),
    }


def test_registry_matches_frozen_schema_v2_snapshot() -> None:
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert registry_snapshot() == expected


def test_registry_invariants_and_extractor_order() -> None:
    raw = registry.raw_feature_ids()
    active = registry.active_feature_ids()
    excluded = registry.excluded_feature_ids()
    statuses = Counter(spec.status for spec in registry.FEATURE_SPECS)
    evidence_scopes = Counter(
        spec.evidence_scope
        for spec in registry.FEATURE_SPECS
        if spec.status is registry.FeatureStatus.ACTIVE
    )
    extractor_columns = tuple(
        column
        for extractor in extract_icon_features.FEATURE_EXTRACTORS
        for column in extractor.columns
    )

    assert len(raw) == len(set(raw)) == 110
    assert len(active) == len(set(active)) == 81
    assert len(excluded) == len(set(excluded)) == 29
    assert set(raw) == set(active) | set(excluded)
    assert set(active).isdisjoint(excluded)
    assert statuses == {
        registry.FeatureStatus.ACTIVE: 81,
        registry.FeatureStatus.AUXILIARY: 3,
        registry.FeatureStatus.DEPRECATED: 7,
        registry.FeatureStatus.EXCLUDED: 19,
    }
    assert evidence_scopes == {
        registry.EvidenceScope.DIRECT: 1,
        registry.EvidenceScope.CONSTRUCT: 77,
        registry.EvidenceScope.CAUTIONARY: 3,
    }
    assert set(registry.feature_evidence()) == set(active)
    assert set(registry.feature_citations()) == set(active)
    assert registry.analysis_feature_ids() == registry.representative_feature_ids()
    assert len(registry.analysis_feature_ids()) == 7
    assert registry.analysis_feature_ids("full_registry") == active
    assert registry.analysis_feature_groups() == tuple(
        (feature_id,) for feature_id in registry.representative_feature_ids()
    )
    assert all(
        spec.evidence_scope is registry.EvidenceScope.NONE
        for spec in registry.FEATURE_SPECS
        if spec.status is not registry.FeatureStatus.ACTIVE
    )
    assert extractor_columns == raw
    assert extract_icon_features.FEATURE_COLUMNS == raw


def test_registry_objects_and_views_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        registry.family_specs()[0].title = "Changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        registry.excluded_feature_reasons()["new"] = "Changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        registry.feature_evidence()["canny_edge_density"] = "Changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        registry.analysis_feature_presets()["new"] = ("canny_edge_density",)  # type: ignore[index]


def test_dashboard_compatibility_adapter_matches_generated_contract() -> None:
    payload = json.loads(DASHBOARD_PAYLOAD.read_text(encoding="utf-8"))

    assert dashboard.image_feature_sections() == payload["metadata"]["image_feature_sections"]
    assert dashboard.IMAGE_FEATURE_COLUMNS == list(registry.raw_feature_ids())
    assert dashboard.active_image_feature_columns() == list(registry.analysis_feature_ids())
    assert dashboard.EXCLUDED_IMAGE_FEATURES == set(registry.excluded_feature_ids())
    assert payload["metadata"]["analysis_feature_preset"] == registry.ANALYSIS_FEATURE_PRESET
    assert payload["metadata"]["image_feature_columns"] == list(registry.analysis_feature_ids())
    assert all(
        feature["evidence"] and feature["citation"] and feature["evidence_scope"]
        for section in payload["metadata"]["image_feature_sections"]
        for feature in section["features"]
    )


def test_similarity_uses_registry_groups_and_preserves_transformed_order() -> None:
    expected_groups: dict[str, list[str]] = {}
    selected_features = frozenset(registry.analysis_feature_ids())
    for family in registry.family_specs():
        columns: list[str] = []
        for feature_id in family.feature_ids:
            if feature_id not in selected_features:
                continue
            if feature_id == similarity.ORIENTATION_COLUMN:
                columns.extend(similarity.ORIENTATION_DERIVED_COLUMNS)
            else:
                columns.append(feature_id)
        if columns:
            expected_groups[family.title] = columns

    expected_transformed = []
    for feature_id in registry.raw_feature_ids():
        if feature_id == similarity.ORIENTATION_COLUMN:
            expected_transformed.extend(similarity.ORIENTATION_DERIVED_COLUMNS)
        else:
            expected_transformed.append(feature_id)

    assert similarity.similarity_feature_groups() == expected_groups
    assert similarity.active_similarity_feature_columns() == [
        column for columns in expected_groups.values() for column in columns
    ]
    assert similarity.similarity_feature_columns() == expected_transformed
    assert "build_analysis_dashboard" not in (
        CODE_DIR / "compute_icon_similarity.py"
    ).read_text(encoding="utf-8")


def test_benchmark_mapping_comes_from_registry_without_contract_drift() -> None:
    assert benchmark.FAMILIES == dict(registry.benchmark_family_features())
