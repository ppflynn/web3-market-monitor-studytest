from __future__ import annotations

import json
from typing import Any, Iterable

from app.config import Settings, get_settings
from app.services.document_loader import DocumentChunk, ProjectDocumentLoader
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import ChromaRagStore


def ingest_project_rag(settings: Settings | None = None, reset: bool = True) -> dict[str, Any]:
    settings = settings or get_settings()
    loader = ProjectDocumentLoader(settings)
    chunks = loader.iter_chunks()
    store = ChromaRagStore(settings)

    if reset:
        store.reset_collection()

    indexed = 0
    embedding_service = EmbeddingService(settings)
    batch_size = max(1, settings.embedding_batch_size)
    for batch in _batched(chunks, batch_size):
        embeddings = embedding_service.embed_texts([chunk.text for chunk in batch])
        indexed += store.upsert_chunks(batch, embeddings)

    return {
        "collection": settings.chroma_collection_name,
        "persist_dir": settings.chroma_persist_dir,
        "reset": reset,
        "files_indexed": len({chunk.relative_path for chunk in chunks}),
        "chunks_indexed": indexed,
    }


def _batched(items: list[DocumentChunk], size: int) -> Iterable[list[DocumentChunk]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


if __name__ == "__main__":
    result = ingest_project_rag()
    print(json.dumps(result, ensure_ascii=False, indent=2))
