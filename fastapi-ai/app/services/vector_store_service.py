from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any

from app.config import Settings
from app.services.document_loader import DocumentChunk


@dataclass(frozen=True)
class ChromaMatch:
    id: str
    document: str
    metadata: dict[str, Any]
    distance: float | None
    score: float


class ChromaRagStore:
    """Persistent Chroma collection for project RAG chunks."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.persist_dir = Path(settings.chroma_persist_dir).expanduser().resolve()
        self.collection_name = settings.chroma_collection_name
        self._client = None
        self._collection = None

    def reset_collection(self) -> None:
        client = self._get_client()
        try:
            client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self._collection = client.get_or_create_collection(name=self.collection_name)

    def upsert_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length.")

        collection = self._get_collection()
        collection.upsert(
            ids=[self.chunk_id(chunk) for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[self.chunk_metadata(chunk) for chunk in chunks],
        )
        return len(chunks)

    def query(self, query_embedding: list[float], n_results: int) -> list[ChromaMatch]:
        if not query_embedding:
            return []

        collection = self._get_collection()
        collection_count = self.count()
        if collection_count == 0:
            return []

        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(max(1, n_results), collection_count),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        matches: list[ChromaMatch] = []
        for index, item_id in enumerate(ids):
            document = documents[index] if index < len(documents) else ""
            metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
            distance = distances[index] if index < len(distances) else None
            matches.append(
                ChromaMatch(
                    id=str(item_id),
                    document=str(document or ""),
                    metadata=dict(metadata),
                    distance=float(distance) if distance is not None else None,
                    score=self._distance_to_score(distance),
                )
            )
        return matches

    def count(self) -> int:
        return int(self._get_collection().count())

    def chunk_id(self, chunk: DocumentChunk) -> str:
        raw = f"{chunk.relative_path}:{chunk.chunk_index}"
        return sha1(raw.encode("utf-8")).hexdigest()

    def chunk_metadata(self, chunk: DocumentChunk) -> dict[str, str | int]:
        return {
            "filename": chunk.filename,
            "chunk_index": chunk.chunk_index,
            "path": chunk.relative_path,
            "title": chunk.title,
            "content_hash": chunk.content_hash,
            "source_type": chunk.source_type,
        }

    def _get_client(self):
        if self._client is None:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            try:
                import chromadb
            except ImportError as exc:
                raise RuntimeError(
                    "chromadb is not installed. Run pip install -r fastapi-ai/requirements.txt."
                ) from exc
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        return self._client

    def _get_collection(self):
        if self._collection is None:
            self._collection = self._get_client().get_or_create_collection(name=self.collection_name)
        return self._collection

    def _distance_to_score(self, distance: Any) -> float:
        if distance is None:
            return 0.0
        try:
            numeric = float(distance)
        except (TypeError, ValueError):
            return 0.0
        return round(1.0 / (1.0 + max(numeric, 0.0)), 4)
