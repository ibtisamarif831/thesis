"""Schema-versioned SQLite embedding cache and experiment history."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


SCHEMA_VERSION = 1


class AIClusteringStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise RuntimeError(f"Unsupported AI clustering database schema {version}")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    model_id TEXT NOT NULL, icon_id TEXT NOT NULL, image_sha256 TEXT NOT NULL,
                    dimension INTEGER NOT NULL, vector BLOB NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (model_id, icon_id, image_sha256)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL,
                    model_id TEXT NOT NULL, family_id TEXT NOT NULL, cohort TEXT NOT NULL,
                    representative_feature_id TEXT NOT NULL, method TEXT NOT NULL,
                    requested_k INTEGER NOT NULL, effective_k INTEGER NOT NULL, seed INTEGER NOT NULL,
                    metrics_json TEXT, usage_json TEXT, cache_hits INTEGER NOT NULL DEFAULT 0,
                    cache_misses INTEGER NOT NULL DEFAULT 0, warning TEXT, error TEXT
                );
                CREATE TABLE IF NOT EXISTS run_items (
                    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                    item_order INTEGER NOT NULL, icon_id TEXT NOT NULL,
                    feature_label INTEGER NOT NULL, ai_label INTEGER,
                    feature_x REAL NOT NULL, feature_y REAL NOT NULL, ai_x REAL, ai_y REAL,
                    PRIMARY KEY (run_id, item_order)
                );
                PRAGMA user_version=1;
            """)

    def get_embedding(self, model_id: str, icon_id: str, image_hash: str) -> np.ndarray | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT dimension, vector FROM embeddings WHERE model_id=? AND icon_id=? AND image_sha256=?",
                (model_id, icon_id, image_hash),
            ).fetchone()
        if not row:
            return None
        vector = np.frombuffer(row["vector"], dtype=np.float32).copy()
        return vector if len(vector) == row["dimension"] else None

    def put_embedding(self, model_id: str, icon_id: str, image_hash: str, vector: np.ndarray) -> None:
        value = np.asarray(vector, dtype=np.float32)
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?, ?, ?)",
                (model_id, icon_id, image_hash, len(value), value.tobytes(), datetime.now(UTC).isoformat()),
            )

    def create_run(self, run: dict[str, object], items: list[dict[str, object]]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO runs (run_id,status,created_at,model_id,family_id,cohort,representative_feature_id,method,requested_k,effective_k,seed) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (run["run_id"], "running", run["created_at"], run["model_id"], run["family_id"], run["cohort"], run["representative_feature_id"], run["method"], run["requested_k"], run["effective_k"], run["seed"]),
            )
            connection.executemany(
                "INSERT INTO run_items (run_id,item_order,icon_id,feature_label,feature_x,feature_y) VALUES (?,?,?,?,?,?)",
                [(run["run_id"], index, item["icon_id"], item["feature_label"], item["feature_x"], item["feature_y"]) for index, item in enumerate(items)],
            )

    def finish_run(self, run_id: str, metrics: dict[str, object], usage: dict[str, object], cache_hits: int, cache_misses: int, warning: str | None, items: list[dict[str, object]]) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE runs SET status='completed',metrics_json=?,usage_json=?,cache_hits=?,cache_misses=?,warning=? WHERE run_id=?",
                (json.dumps(metrics), json.dumps(usage), cache_hits, cache_misses, warning, run_id),
            )
            connection.executemany(
                "UPDATE run_items SET ai_label=?,ai_x=?,ai_y=? WHERE run_id=? AND item_order=?",
                [(item["ai_label"], item["ai_x"], item["ai_y"], run_id, index) for index, item in enumerate(items)],
            )

    def fail_run(self, run_id: str, error: str, cache_hits: int = 0, cache_misses: int = 0) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE runs SET status='failed',error=?,cache_hits=?,cache_misses=? WHERE run_id=?", (error, cache_hits, cache_misses, run_id))

    def list_runs(self, limit: int = 20) -> list[dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 100)),)).fetchall()
        return [self._run_dict(row, include_items=False) for row in rows]

    def counts(self) -> dict[str, int]:
        with self.connect() as connection:
            return {
                "embeddings": connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0],
                "runs": connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
            }

    def get_run(self, run_id: str) -> dict[str, object] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row:
                return None
            items = connection.execute("SELECT * FROM run_items WHERE run_id=? ORDER BY item_order", (run_id,)).fetchall()
        result = self._run_dict(row, include_items=True)
        result["items"] = [{key: item[key] for key in item.keys() if key not in {"run_id", "item_order"}} for item in items]
        return result

    @staticmethod
    def _run_dict(row: sqlite3.Row, include_items: bool) -> dict[str, object]:
        result = {key: row[key] for key in row.keys() if key not in {"metrics_json", "usage_json"}}
        result["metrics"] = json.loads(row["metrics_json"]) if row["metrics_json"] else None
        result["usage"] = json.loads(row["usage_json"]) if row["usage_json"] else None
        if include_items:
            result["items"] = []
        return result
