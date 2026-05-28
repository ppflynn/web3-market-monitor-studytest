from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.config import Settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import ChromaRagStore


@dataclass(frozen=True)
class RagSource:
    title: str
    path: str
    snippet: str
    score: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RagResult:
    context_text: str | None
    sources: list[dict[str, Any]]


class RagService:
    """Chroma-backed project RAG retriever."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_context(self, question: str) -> RagResult:
        if not self.settings.rag_enabled:
            return RagResult(context_text=None, sources=[])
        if not question.strip():
            return RagResult(context_text=None, sources=[])
        if not self.settings.embedding_api_key_value:
            return RagResult(context_text=None, sources=[])

        query_embedding = EmbeddingService(self.settings).embed_query(question)
        matches = ChromaRagStore(self.settings).query(
            query_embedding=query_embedding,
            n_results=self.settings.rag_max_sources,
        )
        if not matches:
            return RagResult(context_text=None, sources=[])

        sources = [
            RagSource(
                title=str(match.metadata.get("title") or match.metadata.get("filename") or match.id),
                path=str(match.metadata.get("path") or match.metadata.get("filename") or match.id),
                snippet=self._clean_snippet(match.document),
                score=match.score,
                metadata=match.metadata,
            )
            for match in matches
            if match.document.strip()
        ]
        if not sources:
            return RagResult(context_text=None, sources=[])

        lines = [
            "[Project RAG context]",
            "Use the following retrieved project files only when they help answer the user. "
            "If the retrieved snippets are insufficient, say what is missing instead of inventing details.",
            "",
        ]
        for index, source in enumerate(sources, start=1):
            chunk_index = source.metadata.get("chunk_index")
            lines.extend(
                [
                    f"Source {index}: {source.path}",
                    f"Chunk index: {chunk_index}" if chunk_index is not None else "Chunk index: unknown",
                    f"Vector score: {source.score}",
                    source.snippet,
                    "",
                ]
            )

        return RagResult(
            context_text="\n".join(lines).strip(),
            sources=[source.__dict__ for source in sources],
        )

    def search(self, question: str) -> list[dict[str, Any]]:
        return self.build_context(question).sources

    def _clean_snippet(self, text: str) -> str:
        snippet = re.sub(r"\n{3,}", "\n\n", text.strip())
        if len(snippet) <= self.settings.rag_snippet_chars:
            return snippet
        return f"{snippet[: self.settings.rag_snippet_chars].rstrip()}..."
