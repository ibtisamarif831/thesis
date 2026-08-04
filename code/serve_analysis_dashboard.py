#!/usr/bin/env python3
"""Serve the generated dashboard and its local AI-clustering API."""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from thesis_pipeline.ai_clustering import AIClusteringService, ServiceConfig
from thesis_pipeline.ai_clustering.service import RequestValidationError


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "icon_data" / "analysis" / "analysis_dashboard"


class DashboardHandler(SimpleHTTPRequestHandler):
    service: AIClusteringService

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/ai-clustering/status":
            self._json(HTTPStatus.OK, self.service.status())
        elif parsed.path == "/api/ai-clustering/runs":
            try:
                limit = int(parse_qs(parsed.query).get("limit", ["20"])[0])
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "limit must be an integer"})
                return
            self._json(HTTPStatus.OK, {"runs": self.service.list_runs(limit)})
        elif parsed.path.startswith("/api/ai-clustering/runs/"):
            run = self.service.get_run(parsed.path.rsplit("/", 1)[-1])
            self._json(HTTPStatus.OK if run else HTTPStatus.NOT_FOUND, run or {"error": "Run not found"})
        elif parsed.path.startswith("/normalized_256/"):
            self._serve_from(ROOT / "icon_data")
        elif parsed.path.startswith("/icon_data/normalized_256/"):
            self._serve_from(ROOT)
        elif parsed.path.startswith("/icon_data/analysis/analysis_dashboard/"):
            self._serve_from(ROOT)
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/ai-clustering/runs":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise RequestValidationError("Request body is too large")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._json(HTTPStatus.CREATED, self.service.run(payload))
        except (RequestValidationError, json.JSONDecodeError, UnicodeDecodeError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except Exception as error:
            self._json(HTTPStatus.BAD_GATEWAY, {"error": str(error)})

    def _json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_from(self, directory: Path) -> None:
        original_directory = self.directory
        self.directory = str(directory)
        try:
            super().do_GET()
        finally:
            self.directory = original_directory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    service = AIClusteringService(ServiceConfig.from_environment(ROOT))
    DashboardHandler.service = service
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard: http://{args.host}:{args.port}")
    print(service.status()["message"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
