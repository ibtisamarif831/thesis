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
    assert "function clearLassoSelection(resetView)" in index
    assert "selectedIconIds.has(item.record.icon_id) ? 0.10 : 0.96" in index
    assert 'class="lasso-icon-button ${item.icon_id === selectedIconId ? "active" : ""}"' in index
    assert "lasso-selected icon${lassoRecords.length === 1 ? \"\" : \"s\"}" in index
    assert 'heading.textContent = lassoRecords.length ? `Lasso Selection (${lassoRecords.length})`' in index
