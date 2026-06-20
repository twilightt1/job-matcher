from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx

from app.ai.embeddings.base import EmbeddingBatchResult, EmbeddingClient
from app.core.config import Settings


class CohereEmbeddingClient(EmbeddingClient):
    """Cohere /v2/embed client for semantic embedding generation."""

    provider = "cohere"

    def __init__(self, settings: Settings) -> None:
        if not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY is required when EMBEDDING_PROVIDER=cohere.")
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self._api_key = settings.cohere_api_key
        self._url = f"{settings.cohere_base_url.rstrip('/')}/v2/embed"
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
            "texts": texts,
            "model": self.model_name,
            "input_type": "search_document",
            "embedding_types": ["float"],
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

        vectors = self._extract_float_embeddings(response.json())
        self._validate_dimensions(vectors)
        return EmbeddingBatchResult(
            provider=self.provider,
            model_name=self.model_name,
            dimension=self.dimension,
            vectors=vectors,
            metadata={
                "runtime": "cohere_api",
                "latency_ms": latency_ms,
                "endpoint": self._url,
            },
        )

    def _extract_float_embeddings(self, response_json: dict[str, Any]) -> list[list[float]]:
        embeddings = response_json.get("embeddings")
        if not isinstance(embeddings, dict):
            raise ValueError("Cohere embed response did not include an embeddings object.")
        float_embeddings = embeddings.get("float")
        if not isinstance(float_embeddings, list):
            raise ValueError("Cohere embed response did not include float embeddings.")
        return [[float(value) for value in vector] for vector in float_embeddings]

    def _validate_dimensions(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            if len(vector) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(vector)}."
                )
