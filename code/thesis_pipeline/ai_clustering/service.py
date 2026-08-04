"""Validated experiment orchestration independent of the HTTP adapter."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from thesis_pipeline.clustering import hierarchical_single_linkage_labels, kmeans, pca_2d

from .metrics import agreement_metrics
from .openrouter import DEFAULT_URL, OpenRouterClient
from .storage import AIClusteringStore


DEFAULT_MODEL = "voyageai/voyage-multimodal-3.5"


class RequestValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ServiceConfig:
    root: Path
    dashboard_data_path: Path
    database_path: Path
    model_id: str = DEFAULT_MODEL
    api_key: str | None = None
    embeddings_url: str = DEFAULT_URL

    @classmethod
    def from_environment(cls, root: Path) -> "ServiceConfig":
        load_dotenv(root / ".env", override=False)
        analysis = root / "icon_data" / "analysis"
        return cls(
            root=root,
            dashboard_data_path=analysis / "analysis_dashboard" / "dashboard_data.json",
            database_path=analysis / "ai_clustering" / "ai_clustering.sqlite3",
            model_id=os.environ.get("OPENROUTER_AI_CLUSTERING_MODEL", DEFAULT_MODEL),
            api_key=os.environ.get("OPENROUTER_API_KEY") or None,
            embeddings_url=os.environ.get("OPENROUTER_EMBEDDINGS_URL", DEFAULT_URL),
        )


class AIClusteringService:
    def __init__(self, config: ServiceConfig, client: object | None = None) -> None:
        self.config = config
        self.store = AIClusteringStore(config.database_path)
        self.client = client or (OpenRouterClient(config.api_key, config.model_id, config.embeddings_url) if config.api_key else None)
        self._run_lock = threading.Lock()

    def status(self) -> dict[str, object]:
        counts = self.store.counts()
        return {
            "configured": self.client is not None,
            "model_id": self.config.model_id,
            "database_path": self.config.database_path.relative_to(self.config.root).as_posix(),
            "message": "Ready to run." if self.client else "Set OPENROUTER_API_KEY in the local server environment to enable AI clustering.",
            "cached_embeddings": counts["embeddings"],
            "saved_runs": counts["runs"],
        }

    def list_runs(self, limit: int = 20) -> list[dict[str, object]]:
        return self.store.list_runs(limit)

    def get_run(self, run_id: str) -> dict[str, object] | None:
        return self.store.get_run(run_id)

    def run(self, payload: object) -> dict[str, object]:
        with self._run_lock:
            return self._run(payload)

    def _run(self, payload: object) -> dict[str, object]:
        request = self._validate_request(payload)
        records = self._record_lookup()
        unknown = [icon_id for icon_id in request["icon_ids"] if icon_id not in records]
        if unknown:
            raise RequestValidationError(f"Unknown icon IDs: {', '.join(unknown[:3])}")
        items = [
            {
                "icon_id": icon_id,
                "feature_label": request["feature_labels"][index],
                "feature_x": request["feature_coords"][index][0],
                "feature_y": request["feature_coords"][index][1],
            }
            for index, icon_id in enumerate(request["icon_ids"])
        ]
        run_id = str(uuid.uuid4())
        effective_k = min(request["requested_k"], len(items))
        warning = f"Requested k={request['requested_k']} exceeds n={len(items)}; using k={effective_k}." if request["requested_k"] > len(items) else None
        run = {
            "run_id": run_id,
            "created_at": datetime.now(UTC).isoformat(),
            "model_id": self.config.model_id,
            "family_id": request["family_id"],
            "cohort": request["cohort"],
            "representative_feature_id": request["representative_feature_id"],
            "method": request["method"],
            "requested_k": request["requested_k"],
            "effective_k": effective_k,
            "seed": request["seed"],
        }
        self.store.create_run(run, items)
        hits = misses = 0
        try:
            if self.client is None:
                raise RuntimeError("OPENROUTER_API_KEY is not configured")
            vectors: list[np.ndarray | None] = []
            missing_images: list[bytes] = []
            missing_positions: list[tuple[int, str, str]] = []
            for index, icon_id in enumerate(request["icon_ids"]):
                image = self._read_normalized_image(records[icon_id])
                image_hash = hashlib.sha256(image).hexdigest()
                vector = self.store.get_embedding(self.config.model_id, icon_id, image_hash)
                vectors.append(vector)
                if vector is None:
                    misses += 1
                    missing_images.append(image)
                    missing_positions.append((index, icon_id, image_hash))
                else:
                    hits += 1
            usage: dict[str, object] = {}
            if missing_images:
                response = self.client.embed_images(missing_images)
                usage = response.usage
                for (index, icon_id, image_hash), vector in zip(missing_positions, response.vectors, strict=True):
                    vectors[index] = vector
                    self.store.put_embedding(self.config.model_id, icon_id, image_hash, vector)
            matrix = np.vstack([vector for vector in vectors if vector is not None]).astype(float)
            if len(matrix) != len(items):
                raise RuntimeError("Embedding matrix could not be assembled")
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise RuntimeError("OpenRouter returned a zero-length embedding")
            matrix = matrix / norms
            coords = pca_2d(matrix)
            if request["method"] == "hierarchical":
                labels = hierarchical_single_linkage_labels(matrix, (effective_k,))[effective_k]
            else:
                labels, _ = kmeans(matrix, effective_k, request["seed"])
            ai_labels = [int(value) for value in labels]
            for index, item in enumerate(items):
                item.update(ai_label=ai_labels[index], ai_x=float(coords[index, 0]), ai_y=float(coords[index, 1]))
            metrics = agreement_metrics(request["feature_labels"], ai_labels)
            self.store.finish_run(run_id, metrics, usage, hits, misses, warning, items)
        except Exception as error:
            self.store.fail_run(run_id, str(error), hits, misses)
            raise
        result = self.store.get_run(run_id)
        if result is None:
            raise RuntimeError("Completed run was not persisted")
        return result

    def _record_lookup(self) -> dict[str, dict[str, object]]:
        payload = json.loads(self.config.dashboard_data_path.read_text(encoding="utf-8"))
        records = payload.get("feature_group_records") or payload.get("records") or []
        return {record["icon_id"]: record for record in records}

    def _read_normalized_image(self, record: dict[str, object]) -> bytes:
        raw_path = str(record.get("normalized_path", ""))
        dashboard_dir = self.config.dashboard_data_path.parent
        image_path = (dashboard_dir / raw_path).resolve()
        allowed = (self.config.root / "icon_data" / "normalized_256").resolve()
        if image_path != allowed and allowed not in image_path.parents:
            raise RequestValidationError("Resolved image path is outside normalized image storage")
        return image_path.read_bytes()

    @staticmethod
    def _validate_request(payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise RequestValidationError("Request body must be a JSON object")
        icon_ids = payload.get("icon_ids")
        labels = payload.get("feature_labels")
        coords = payload.get("feature_coords")
        if not isinstance(icon_ids, list) or not icon_ids or not all(isinstance(value, str) and value for value in icon_ids):
            raise RequestValidationError("icon_ids must be a non-empty string array")
        if len(set(icon_ids)) != len(icon_ids):
            raise RequestValidationError("icon_ids must be unique")
        if not isinstance(labels, list) or len(labels) != len(icon_ids) or not all(isinstance(value, int) for value in labels):
            raise RequestValidationError("feature_labels must contain one integer per icon")
        if not isinstance(coords, list) or len(coords) != len(icon_ids):
            raise RequestValidationError("feature_coords must contain one coordinate pair per icon")
        try:
            clean_coords = [[float(pair[0]), float(pair[1])] for pair in coords if isinstance(pair, list) and len(pair) == 2]
        except (TypeError, ValueError):
            clean_coords = []
        if len(clean_coords) != len(icon_ids) or not np.isfinite(clean_coords).all():
            raise RequestValidationError("feature_coords must contain finite numeric pairs")
        method = payload.get("method")
        if method not in {"kmeans", "hierarchical"}:
            raise RequestValidationError("method must be kmeans or hierarchical")
        requested_k = payload.get("requested_k")
        if not isinstance(requested_k, int) or requested_k < 1:
            raise RequestValidationError("requested_k must be a positive integer")
        seed = payload.get("seed", 42)
        if seed != 42:
            raise RequestValidationError("AI clustering seed must be 42")
        for field in ("family_id", "cohort", "representative_feature_id"):
            if not isinstance(payload.get(field), str) or not payload[field]:
                raise RequestValidationError(f"{field} is required")
        return {
            "icon_ids": icon_ids, "feature_labels": labels, "feature_coords": clean_coords,
            "method": method, "requested_k": requested_k, "seed": seed,
            "family_id": payload["family_id"], "cohort": payload["cohort"],
            "representative_feature_id": payload["representative_feature_id"],
        }
