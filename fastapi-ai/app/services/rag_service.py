from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re
from typing import Any

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
class RagSource:
    title: str
    path: str
    snippet: str
    score: float


@dataclass(frozen=True)
class RagResult:
    context_text: str | None
    sources: list[dict[str, Any]]


@dataclass(frozen=True)
class _Chunk:
    title: str
    path: Path
    text: str


class RagService:
    """Small local-code RAG retriever for the first project Q&A version."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = self._resolve_root()
        self.include_paths = self._split_csv(settings.rag_include_paths)
        self.exclude_dirs = set(self._split_csv(settings.rag_exclude_dirs))

    def build_context(self, question: str) -> RagResult:
        if not self.settings.rag_enabled:
            return RagResult(context_text=None, sources=[])

        query_terms = self._query_terms(question)
        if not query_terms:
            return RagResult(context_text=None, sources=[])

        scored: list[tuple[float, _Chunk]] = []
        for chunk in self._iter_chunks():
            score = self._score_chunk(chunk, query_terms, question)
            if score >= self.settings.rag_min_score:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[: self.settings.rag_max_sources]
        if not top:
            return RagResult(context_text=None, sources=[])

        sources = [
            RagSource(
                title=chunk.title,
                path=self._display_path(chunk.path),
                snippet=self._clean_snippet(chunk.text),
                score=round(score, 4),
            )
            for score, chunk in top
        ]

        lines = [
            "[Project RAG context]",
            "Use the following retrieved project files only when they help answer the user. "
            "If the retrieved snippets are insufficient, say what is missing instead of inventing details.",
            "",
        ]
        for index, source in enumerate(sources, start=1):
            lines.extend(
                [
                    f"Source {index}: {source.path}",
                    f"Relevance score: {source.score}",
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

    def _iter_chunks(self) -> list[_Chunk]:
        chunks: list[_Chunk] = []
        for file_path in self._iter_files():
            text = self._read_text(file_path)
            if not text:
                continue
            for index, chunk_text in enumerate(self._chunk_text(text), start=1):
                title = f"{self._display_path(file_path)}#{index}"
                chunks.append(_Chunk(title=title, path=file_path, text=chunk_text))
        return chunks

    def _iter_files(self) -> list[Path]:
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
        return sorted(set(files), key=lambda path: self._display_path(path))

    def _chunk_text(self, text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
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

    def _fixed_chunks(self, text: str) -> list[str]:
        size = self.settings.rag_chunk_chars
        overlap = min(180, max(0, size // 8))
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start : start + size])
            start += size - overlap
        return chunks

    def _score_chunk(self, chunk: _Chunk, query_terms: list[str], question: str) -> float:
        text = f"{chunk.path.name}\n{chunk.text}".lower()
        score = 0.0
        for term in query_terms:
            lowered = term.lower()
            if not lowered:
                continue
            count = text.count(lowered)
            if count:
                score += min(count, 6) * (2.0 if len(lowered) > 2 else 0.8)

        path_text = self._display_path(chunk.path).lower()
        for term in query_terms:
            lowered = term.lower()
            if lowered and lowered in path_text:
                score += 3.0

        sample = chunk.text[:1200].lower()
        ratio = SequenceMatcher(None, question.lower()[:300], sample).ratio()
        return score + ratio

    def _query_terms(self, question: str) -> list[str]:
        terms = re.findall(r"[A-Za-z0-9_./-]{2,}", question)
        han_chars = re.findall(r"[\u4e00-\u9fff]", question)
        terms.extend(han_chars)
        terms.extend("".join(han_chars[index : index + 2]) for index in range(len(han_chars) - 1))
        return list(dict.fromkeys(term for term in terms if term.strip()))

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

    def _display_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _clean_snippet(self, text: str) -> str:
        snippet = re.sub(r"\n{3,}", "\n\n", text.strip())
        if len(snippet) <= self.settings.rag_snippet_chars:
            return snippet
        return f"{snippet[: self.settings.rag_snippet_chars].rstrip()}..."

    def _split_csv(self, value: str) -> list[str]:
        return [item.strip().strip("/\\") for item in value.split(",") if item.strip()]
