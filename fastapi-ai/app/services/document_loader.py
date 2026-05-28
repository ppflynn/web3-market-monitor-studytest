from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import re

from app.config import Settings


TEXT_SUFFIXES = {
    ".java",
    ".js",
    ".json",
    ".md",
    ".properties",
    ".py",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class DocumentChunk:
    title: str
    path: Path
    relative_path: str
    filename: str
    chunk_index: int
    text: str
    content_hash: str
    source_type: str


class ProjectDocumentLoader:
    """Loads project text files and turns them into stable RAG chunks."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = self._resolve_root()
        self.include_paths = self._split_csv(settings.rag_include_paths)
        self.exclude_dirs = set(self._split_csv(settings.rag_exclude_dirs))

    def iter_chunks(self) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for file_path in self.iter_files():
            text = self._read_text(file_path)
            if not text:
                continue

            relative_path = self.display_path(file_path)
            for index, chunk_text in enumerate(self.chunk_text(text), start=1):
                chunks.append(
                    DocumentChunk(
                        title=f"{relative_path}#{index}",
                        path=file_path,
                        relative_path=relative_path,
                        filename=file_path.name,
                        chunk_index=index,
                        text=chunk_text,
                        content_hash=self._hash_text(chunk_text),
                        source_type=file_path.suffix.lower().lstrip(".") or "text",
                    )
                )
        return chunks

    def iter_files(self) -> list[Path]:
        files: list[Path] = []
        for include in self.include_paths:
            candidate = (self.root / include).resolve()
            if not self._is_under_root(candidate) or not candidate.exists():
                continue
            if candidate.is_file():
                if self._is_supported_file(candidate):
                    files.append(candidate)
                continue

            for path in candidate.rglob("*"):
                if len(files) >= self.settings.rag_max_files:
                    break
                if path.is_file() and self._is_supported_file(path) and not self._is_excluded(path):
                    files.append(path)
        return sorted(set(files), key=lambda path: self.display_path(path))

    def chunk_text(self, text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []
        if len(normalized) <= self.settings.rag_chunk_chars:
            return [normalized]

        blocks = re.split(r"\n\s*\n", normalized)
        chunks: list[str] = []
        current = ""
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if len(block) > self.settings.rag_chunk_chars:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._fixed_chunks(block))
                continue

            candidate = f"{current}\n\n{block}".strip() if current else block
            if len(candidate) > self.settings.rag_chunk_chars:
                if current:
                    chunks.append(current)
                current = block
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

    def display_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _fixed_chunks(self, text: str) -> list[str]:
        size = self.settings.rag_chunk_chars
        overlap = min(180, max(0, size // 8))
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start : start + size])
            start += size - overlap
        return chunks

    def _read_text(self, path: Path) -> str | None:
        try:
            if path.stat().st_size > self.settings.rag_max_file_bytes:
                return None
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _is_supported_file(self, path: Path) -> bool:
        return path.suffix.lower() in TEXT_SUFFIXES

    def _is_excluded(self, path: Path) -> bool:
        return any(part in self.exclude_dirs for part in path.parts)

    def _is_under_root(self, path: Path) -> bool:
        try:
            path.relative_to(self.root)
            return True
        except ValueError:
            return False

    def _resolve_root(self) -> Path:
        if self.settings.rag_root_path:
            configured = Path(self.settings.rag_root_path).expanduser().resolve()
            if configured.exists():
                return configured

        cwd = Path.cwd().resolve()
        if (cwd / "pom.xml").exists():
            return cwd

        service_file = Path(__file__).resolve()
        for parent in service_file.parents:
            if (parent / "pom.xml").exists() or (parent / "fastapi-ai").exists():
                return parent
        return service_file.parents[2]

    def _hash_text(self, text: str) -> str:
        return sha1(text.encode("utf-8")).hexdigest()

    def _split_csv(self, value: str) -> list[str]:
        return [item.strip().strip("/\\") for item in value.split(",") if item.strip()]
