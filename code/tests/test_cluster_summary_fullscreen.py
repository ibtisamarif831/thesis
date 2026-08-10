from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard


def test_cluster_summary_moves_heatmap_and_all_details_into_modal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'id="clusterModal"' in index
    assert 'class="cluster-dialog"' in index
    assert ".cluster-dialog { width: 100vw; height: 100vh; height: 100dvh;" in index
    assert "Show heatmap" in index
    assert index.count("View all cluster details") == 2
    assert "openClusterAnalysisModal(" in index
    assert 'class="cluster-analysis-list"' in index
    assert 'class="summary-cluster" open' in index
    assert "function clusterDetailCardHtml(" in index
    assert index.count("return clusterDetailCardHtml({") == 2
    assert "Every cluster is expanded below" in index
    assert "members.map(item =>" in index
    assert 'event.key === "Escape"' in index
    assert "clusterModalReturnFocus.focus()" in index


def test_clustering_left_sidebar_is_collapsible(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'id="clusteringSidebar"' in index
    assert 'id="sidebarToggle"' in index
    assert 'aria-controls="clusteringSidebar"' in index
    assert 'aria-expanded="true"' in index
    assert 'view.classList.toggle("controls-collapsed")' in index
    assert 'button.textContent = collapsed ? "Show sidebar" : "Hide sidebar"' in index
    assert '#clusteringView.controls-collapsed > .clustering-sidebar { display: none; }' in index


def test_ai_analysis_sidebar_is_collapsible(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'id="aiWorkspace"' in index
    assert 'id="aiAnalysisSidebar"' in index
    assert 'id="aiSidebarToggle"' in index
    assert 'aria-controls="aiAnalysisSidebar"' in index
    assert 'workspace.classList.toggle("ai-sidebar-collapsed")' in index
    assert '.ai-workspace.ai-sidebar-collapsed > .ai-analysis { display: none; }' in index
    assert 'Plotly.Plots.resize(document.getElementById("aiEmbeddingScatter"))' in index
