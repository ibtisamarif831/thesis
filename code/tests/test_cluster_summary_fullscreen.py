from __future__ import annotations

import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import build_analysis_dashboard as dashboard


def test_cluster_summary_supports_fullscreen_all_icon_gallery(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", tmp_path)

    dashboard.write_index_html()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'id="clusterModal"' in index
    assert 'class="cluster-dialog"' in index
    assert ".cluster-dialog { width: 100vw; height: 100vh; height: 100dvh;" in index
    assert "View all ${items.length} icons fullscreen" in index
    assert "items.map(item =>" in index
    assert "openClusterModal(entry[0], entry[1], button)" in index
    assert 'event.key === "Escape"' in index
    assert "clusterModalReturnFocus.focus()" in index
