from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard


def test_clustering_chart_supports_free_form_lasso_selection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'id="lassoMode"' in index
    assert 'id="zoomMode"' in index
    assert 'id="clearLassoSelection"' in index
    assert 'id="resetPlotView"' in index
    assert 'dragMode: "lasso"' in index
    assert 'dragmode: state.dragMode' in index
    assert 'modeBarButtonsToAdd: ["lasso2d", "select2d"]' in index
    assert 'scatter.on("plotly_selected", event => applyLassoSelection(event))' in index


def test_lasso_selection_zooms_dims_and_renders_icon_details(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "function applyLassoSelection(event)" in index
    assert "function zoomToSelectedPoints(points)" in index
    assert "function clearLassoSelection()" in index
    assert "function resetPlotView()" in index
    assert 'document.getElementById("clearLassoSelection").addEventListener("click", clearLassoSelection)' in index
    assert 'document.getElementById("resetPlotView").addEventListener("click", resetPlotView)' in index
    assert 'if (currentPlotContext) render()' in index
    assert 'Plotly.restyle("scatter", {selectedpoints: [null]})' not in index
    assert "selectedIconIds.has(item.record.icon_id) ? 0.10 : 0.96" in index
    assert 'class="lasso-icon-button ${item.icon_id === selectedIconId ? "active" : ""}"' in index
    assert "lasso-selected icon${lassoRecords.length === 1 ? \"\" : \"s\"}" in index
    assert 'heading.textContent = lassoRecords.length ? `Lasso Selection (${lassoRecords.length})`' in index


def test_icon_and_lasso_details_compare_features_with_full_sample(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "function featureDistribution(records, featureId)" in index
    assert "function featurePercentile(value, distribution)" in index
    assert "function featureComparisonCardHtml(" in index
    assert 'if (compact) return `<div class="feature-value-card compact">' in index
    assert "#hoverPreview .feature-value-head b:last-child { color: #fff; }" in index
    assert "All ${populationSize} icons: median" in index
    assert "middle 50%" in index
    assert "from median" in index
    assert "feature-range-marker global" in index
    assert "feature-range-marker subject" in index
    assert "function lassoFeatureComparisonHtml(selectedRecords, allRecords, featureIds)" in index
    assert "Selected group vs all ${allRecords.length} icons" in index
    assert "lassoFeatureComparisonHtml(lassoRecords, records, representativeFeatureIds())" in index
    assert "renderHoverPreview(record, labels[records.indexOf(record)], event.event, records)" in index
    assert "groupedFeatureHtml(record, representativeFeatureIds(), false, null, records, true)" in index
    assert "groupedFeatureHtml(record, selectedFeatureIds(), false, 10, comparisonRecords, true)" in index
    assert "groupedFeatureHtml(record, representativeFeatureIds(), false, null, items, true)" in index
