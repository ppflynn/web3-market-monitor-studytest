from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from app.config import Settings


class EmbeddingService:
    """OpenAI-compatible embedding client used by Chroma ingestion and query."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        cleaned = [text.strip() for text in texts]
        if not cleaned:
            return []

        api_key = self.settings.embedding_api_key_value
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Embedding API key is not configured. Set EMBEDDING_API_KEY or AI_API_KEY.",
            )

        payload = {
            "model": self.settings.embedding_model,
            "input": cleaned,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.settings.embedding_timeout_seconds) as client:
                response = client.post(
                    self.settings.embeddings_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._safe_error_detail(exc.response)
            raise HTTPException(status_code=502, detail=detail) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Embedding provider request failed: {exc.__class__.__name__}",
            ) from exc

        return self._extract_embeddings(response.json(), expected_count=len(cleaned))

    def embed_query(self, text: str) -> list[float]:
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []

    def _extract_embeddings(self, data: dict[str, Any], expected_count: int) -> list[list[float]]:
        items = data.get("data")
        if not isinstance(items, list):
            raise HTTPException(status_code=502, detail="Embedding provider returned no data list.")

        def item_index(item: dict[str, Any], fallback: int) -> int:
            value = item.get("index")
            return value if isinstance(value, int) else fallback

        ordered = sorted(
            (item for item in items if isinstance(item, dict)),
            key=lambda item: item_index(item, 0),
        )
        embeddings = [item.get("embedding") for item in ordered]
        if len(embeddings) != expected_count or not all(isinstance(item, list) for item in embeddings):
            raise HTTPException(status_code=502, detail="Embedding provider returned malformed embeddings.")
        return embeddings

    def _safe_error_detail(self, response: httpx.Response) -> str:
        text = response.text[:500]
        return f"Embedding provider returned HTTP {response.status_code}: {text}"
