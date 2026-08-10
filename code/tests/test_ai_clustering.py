from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

import numpy as np

from thesis_pipeline.ai_clustering.metrics import agreement_metrics, cluster_variance_profile
from thesis_pipeline.ai_clustering.openrouter import EmbeddingResponse, OpenRouterClient, OpenRouterError, image_embedding_payload
from thesis_pipeline.ai_clustering.service import AIClusteringService, RequestValidationError, ServiceConfig
from serve_analysis_dashboard import DashboardHandler


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[list[bytes]] = []

    def embed_images(self, images: list[bytes]) -> EmbeddingResponse:
        self.calls.append(images)
        vectors = [np.array([float(index + 1), 1.0, float((index + 1) % 2)], dtype=np.float32) for index in range(len(images))]
        return EmbeddingResponse(vectors, {"prompt_tokens": len(images)})


def make_service(tmp_path: Path, client: FakeClient | None = None) -> tuple[AIClusteringService, dict[str, object]]:
    dashboard_dir = tmp_path / "icon_data" / "analysis" / "analysis_dashboard"
    image_dir = tmp_path / "icon_data" / "normalized_256"
    dashboard_dir.mkdir(parents=True)
    image_dir.mkdir(parents=True)
    records = []
    for index in range(4):
        icon_id = f"icon-{index}"
        (image_dir / f"{icon_id}.png").write_bytes(b"png" + bytes([index]))
        records.append({"icon_id": icon_id, "normalized_path": f"../../normalized_256/{icon_id}.png"})
    data_path = dashboard_dir / "dashboard_data.json"
    data_path.write_text(json.dumps({"feature_group_records": records}), encoding="utf-8")
    config = ServiceConfig(
        root=tmp_path,
        dashboard_data_path=data_path,
        database_path=tmp_path / "icon_data" / "analysis" / "ai_clustering" / "ai_clustering.sqlite3",
        api_key="test-key",
    )
    payload = {
        "family_id": "complexity",
        "cohort": "all",
        "representative_feature_id": "component_count_v2",
        "method": "kmeans",
        "requested_k": 2,
        "seed": 42,
        "icon_ids": [record["icon_id"] for record in records],
        "feature_labels": [0, 0, 1, 1],
        "feature_coords": [[-1.0, 0.0], [-0.5, 0.2], [0.5, -0.2], [1.0, 0.0]],
    }
    return AIClusteringService(config, client=client or FakeClient()), payload


def test_openrouter_payload_contains_only_images() -> None:
    payload = image_embedding_payload("model", [b"first", b"second"])
    serialized = json.dumps(payload)
    assert payload["model"] == "model"
    assert len(payload["input"]) == 2
    assert "data:image/png;base64," in serialized
    for forbidden in ("icon_id", "label", "family", "cohort", "feature"):
        assert forbidden not in serialized


def test_openrouter_rejects_malformed_and_inconsistent_vectors() -> None:
    with np.testing.assert_raises(OpenRouterError):
        OpenRouterClient._parse_response({"invalid": []}, 1)
    with np.testing.assert_raises(OpenRouterError):
        OpenRouterClient._parse_response({"data": [{"embedding": [1, 2]}, {"embedding": [1]}]}, 2)


def test_openrouter_sdk_receives_multimodal_image_input() -> None:
    calls: list[dict[str, object]] = []

    class Embeddings:
        def generate(self, **kwargs: object) -> dict[str, object]:
            calls.append(kwargs)
            return {"data": [{"index": 0, "embedding": [1.0, 2.0]}]}

    class SDKClient:
        embeddings = Embeddings()

    result = OpenRouterClient("secret", "model", sdk_client=SDKClient()).embed_images([b"png"])
    assert calls[0]["model"] == "model"
    assert "data:image/png;base64," in json.dumps(calls[0]["input"])
    assert result.vectors[0].tolist() == [1.0, 2.0]


def test_metrics_are_invariant_to_cluster_number_permutations() -> None:
    feature = [0, 0, 1, 1, 2, 2]
    ai = [5, 5, 9, 9, 7, 7]
    metrics = agreement_metrics(feature, ai)
    assert metrics["adjusted_rand_index"] == 1.0
    assert metrics["normalized_mutual_information"] == 1.0
    assert metrics["pairwise_same_cluster_agreement"] == 1.0


def test_cluster_variance_profile_separates_size_and_strength() -> None:
    matrix = np.array([[-3.0], [-3.0], [1.0], [1.0], [1.0], [1.0]])
    profile = cluster_variance_profile(matrix, [0, 0, 1, 1, 1, 1])
    assert sum(item["variance_contribution"] for item in profile) == 1.0
    assert profile[0]["separation_strength"] > profile[1]["separation_strength"]
    assert profile[0]["variance_contribution"] > profile[1]["variance_contribution"]


def test_run_is_persisted_and_second_run_uses_cache(tmp_path: Path) -> None:
    client = FakeClient()
    service, payload = make_service(tmp_path, client)
    first = service.run(payload)
    second = service.run(payload)
    assert first["status"] == second["status"] == "completed"
    assert first["cache_misses"] == 4
    assert second["cache_hits"] == 4
    assert len(client.calls) == 1
    assert [item["icon_id"] for item in first["items"]] == payload["icon_ids"]
    assert np.isclose(sum(item["variance_contribution"] for item in first["metrics"]["embedding_cluster_profile"]), 1.0)
    assert service.get_run(first["run_id"])["metrics"] == first["metrics"]
    assert len(service.list_runs()) == 2
    with sqlite3.connect(service.config.database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


def test_image_hash_change_invalidates_only_that_embedding(tmp_path: Path) -> None:
    client = FakeClient()
    service, payload = make_service(tmp_path, client)
    service.run(payload)
    image = tmp_path / "icon_data" / "normalized_256" / "icon-2.png"
    image.write_bytes(b"changed")
    result = service.run(payload)
    assert result["cache_hits"] == 3
    assert result["cache_misses"] == 1
    assert len(client.calls) == 2
    assert len(client.calls[-1]) == 1


def test_old_run_is_enriched_from_cache_without_database_rewrite(tmp_path: Path) -> None:
    service, payload = make_service(tmp_path)
    result = service.run(payload)
    legacy_metrics = agreement_metrics(payload["feature_labels"], [item["ai_label"] for item in result["items"]])
    with sqlite3.connect(service.config.database_path) as connection:
        connection.execute("UPDATE runs SET metrics_json=? WHERE run_id=?", (json.dumps(legacy_metrics), result["run_id"]))
    enriched = service.get_run(result["run_id"])
    assert enriched is not None
    assert "embedding_cluster_profile" in enriched["metrics"]
    with sqlite3.connect(service.config.database_path) as connection:
        persisted = json.loads(connection.execute("SELECT metrics_json FROM runs WHERE run_id=?", (result["run_id"],)).fetchone()[0])
    assert "embedding_cluster_profile" not in persisted


def test_failed_run_is_saved_and_arbitrary_ids_are_rejected(tmp_path: Path) -> None:
    class FailingClient(FakeClient):
        def embed_images(self, images: list[bytes]) -> EmbeddingResponse:
            raise OpenRouterError("provider unavailable")

    service, payload = make_service(tmp_path, FailingClient())
    with np.testing.assert_raises(OpenRouterError):
        service.run(payload)
    assert service.list_runs()[0]["status"] == "failed"
    bad_payload = dict(payload, icon_ids=["../../secret", *payload["icon_ids"][1:]])
    with np.testing.assert_raises(RequestValidationError):
        service.run(bad_payload)


def test_k_above_sample_size_is_capped_with_warning(tmp_path: Path) -> None:
    service, payload = make_service(tmp_path)
    result = service.run(dict(payload, requested_k=99))
    assert result["requested_k"] == 99
    assert result["effective_k"] == 4
    assert "using k=4" in result["warning"]


def test_generated_dashboard_contains_ai_clustering_contract() -> None:
    html = (Path(__file__).parents[2] / "icon_data" / "analysis" / "analysis_dashboard" / "index.html").read_text(encoding="utf-8")
    for expected in (
        "AI Clustering",
        "Run AI Clustering",
        "Open feature vs AI comparison",
        'id="aiComparisonModal"',
        'id="aiFeatureContributions"',
        'id="aiClusterSummary"',
        'id="aiIconDetail"',
        "aiFeatureSeparation",
        "clusterInterpretationProfile",
        "Variance contribution",
        "Separation strength",
        "Embedding variance",
        "Measured variance",
        "AI clusters by measured feature",
        "Icon statistics",
        "Feature statistics",
        "Share of sample",
        "Cluster mean",
        "Overall mean",
        "aiFeatureScatter",
        "aiEmbeddingScatter",
        "/api/ai-clustering/runs",
    ):
        assert expected in html
    assert "between-cluster variance" in html
    assert "the embedding model did not receive these feature values" in html
    assert "const PLOT_ICON_SCALE = 0.055" in html
    assert html.count("ranges.spanX * PLOT_ICON_SCALE") == 2
    assert html.count("ranges.spanY * PLOT_ICON_SCALE") == 2
    assert "Adjusted Rand index" not in html
    assert "Normalized mutual information" not in html
    assert "Reported usage" not in html


def test_dashboard_server_supports_both_normalized_image_url_forms() -> None:
    DashboardHandler.service = object()  # The static-image routes do not access the service.
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        data_path = Path(__file__).parents[2] / "icon_data" / "analysis" / "analysis_dashboard" / "dashboard_data.json"
        record = json.loads(data_path.read_text(encoding="utf-8"))["records"][0]
        relative = record["normalized_path"].split("normalized_256/", 1)[1]
        base = f"http://127.0.0.1:{server.server_port}"
        for prefix in ("/normalized_256/", "/icon_data/normalized_256/"):
            with urlopen(base + prefix + relative) as response:
                assert response.status == 200
                assert response.headers.get_content_type() == "image/png"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
