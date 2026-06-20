from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx

from app.ai.embeddings.base import EmbeddingBatchResult, EmbeddingClient
from app.core.config import Settings


class JinaEmbeddingClient(EmbeddingClient):
    """Jina AI embeddings API client for semantic embedding generation."""

    provider = "jina"

    def __init__(self, settings: Settings) -> None:
        if not settings.jina_api_key:
            raise ValueError("JINA_API_KEY is required when EMBEDDING_PROVIDER=jina.")
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._api_key = settings.jina_api_key
        self._url = f"{settings.jina_base_url.rstrip('/')}/v1/embeddings"
        self._timeout = settings.embedding_request_timeout_seconds

    def embed_texts(self, texts: list[str]) -> EmbeddingBatchResult:
        if not texts:
            return EmbeddingBatchResult(
                provider=self.provider,
                model_name=self.model_name,
                dimension=self.dimension,
                vectors=[],
            )

        payload = {
            "model": self.model_name,
            "task": "retrieval.passage",
            "normalized": True,
            "input": texts,
        }
        started_at = perf_counter()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                self._url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        latency_ms = max(0, round((perf_counter() - started_at) * 1000))
        response.raise_for_status()

        raw_vectors = self._extract_embeddings(response.json())
        vectors = self._coerce_dimensions(raw_vectors)
        self._validate_dimensions(vectors)
        return EmbeddingBatchResult(
            provider=self.provider,
            model_name=self.model_name,
            dimension=self.dimension,
            vectors=vectors,
            metadata={
                "runtime": "jina_api",
                "latency_ms": latency_ms,
                "endpoint": self._url,
                "requested_dimensions": self.dimension,
                "source_dimension": len(raw_vectors[0]) if raw_vectors else self.dimension,
            },
        )

    def _extract_embeddings(self, response_json: dict[str, Any]) -> list[list[float]]:
        data = response_json.get("data")
        if not isinstance(data, list):
            raise ValueError("Jina embeddings response did not include a data list.")
        vectors: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Jina embeddings response data item was not an object.")
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise ValueError("Jina embeddings response item did not include an embedding list.")
            vectors.append([float(value) for value in embedding])
        return vectors

    def _coerce_dimensions(self, vectors: list[list[float]]) -> list[list[float]]:
        coerced_vectors: list[list[float]] = []
        for vector in vectors:
            if len(vector) > self.dimension:
                coerced_vectors.append(vector[: self.dimension])
            elif len(vector) < self.dimension:
                coerced_vectors.append(vector + [0.0] * (self.dimension - len(vector)))
            else:
                coerced_vectors.append(vector)
        return [self._normalize(vector) for vector in coerced_vectors]

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]

    def _validate_dimensions(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            if len(vector) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(vector)}."
                )
