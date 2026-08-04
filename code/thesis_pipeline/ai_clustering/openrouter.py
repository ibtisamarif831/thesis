"""OpenRouter SDK adapter for multimodal image embeddings."""

from __future__ import annotations

import base64
from dataclasses import dataclass

import numpy as np
from openrouter import OpenRouter, errors as openrouter_errors


DEFAULT_URL = "https://openrouter.ai/api/v1/embeddings"


class OpenRouterError(RuntimeError):
    """A provider or response validation error safe to persist."""


def image_embedding_payload(model_id: str, images: list[bytes]) -> dict[str, object]:
    return {
        "model": model_id,
        "input": [
            {"content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(image).decode('ascii')}"}}]}
            for image in images
        ],
    }


@dataclass
class EmbeddingResponse:
    vectors: list[np.ndarray]
    usage: dict[str, object]


class OpenRouterClient:
    def __init__(self, api_key: str, model_id: str, url: str = DEFAULT_URL, sdk_client: object | None = None) -> None:
        self.model_id = model_id
        self.url = url
        server_url = url.removesuffix("/embeddings")
        self._client = sdk_client or OpenRouter(api_key=api_key, server_url=server_url, timeout_ms=120_000)

    def embed_images(self, images: list[bytes]) -> EmbeddingResponse:
        if not images:
            return EmbeddingResponse([], {})
        payload = image_embedding_payload(self.model_id, images)
        try:
            response = self._client.embeddings.generate(model=self.model_id, input=payload["input"])
        except (openrouter_errors.OpenRouterError, openrouter_errors.NoResponseError) as error:
            raise OpenRouterError(f"OpenRouter request failed: {error}") from error
        parsed = response.model_dump(mode="python") if hasattr(response, "model_dump") else response
        return self._parse_response(parsed, len(images))

    @staticmethod
    def _parse_response(payload: object, expected: int) -> EmbeddingResponse:
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise OpenRouterError("OpenRouter response has no embedding data")
        if not all(isinstance(row, dict) for row in payload["data"]):
            raise OpenRouterError("OpenRouter returned malformed embedding rows")
        rows = sorted(payload["data"], key=lambda row: row.get("index", 0))
        if len(rows) != expected:
            raise OpenRouterError("OpenRouter returned an unexpected embedding count")
        vectors = []
        dimension = None
        for row in rows:
            vector = np.asarray(row.get("embedding"), dtype=np.float32)
            if vector.ndim != 1 or not len(vector) or not np.isfinite(vector).all():
                raise OpenRouterError("OpenRouter returned an invalid embedding")
            dimension = len(vector) if dimension is None else dimension
            if len(vector) != dimension:
                raise OpenRouterError("OpenRouter returned inconsistent embedding dimensions")
            vectors.append(vector)
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        return EmbeddingResponse(vectors, usage)
