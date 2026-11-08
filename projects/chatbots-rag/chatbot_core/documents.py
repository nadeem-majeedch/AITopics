"""Document loading, section splitting, and chunking with metadata.

This module is deliberately independent of any model. It turns Markdown or plain
text files into chunks that carry enough metadata to cite them, filter them, and
debug retrieval.

Design rules enforced here:

* chunk on headings first, then on length;
* keep the document title, section heading, source path, and offsets;
* include a small overlap so a fact on a boundary survives;
* never read files outside the directory handed to ``load_documents``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
WORD = re.compile(r"[A-Za-z0-9']+")

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}


@dataclass(frozen=True)
class Document:
    """One source file, split into title and sections."""

    doc_id: str
    title: str
    source: str
    sections: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def text(self) -> str:
        return "\n\n".join(body for _, body in self.sections)


@dataclass(frozen=True)
class Chunk:
    """A retrievable unit of text with citation metadata."""

    chunk_id: str
    doc_id: str
    title: str
    section: str
    text: str
    source: str
    start: int
    end: int

    @property
    def retrieval_text(self) -> str:
        """Text indexed for search: heading context plus body.

        The body alone cannot match a query that names the section ("module
        assessment weights" against a section titled "Module weights"), which is
        a real and easily replicated retrieval failure. The citation still shows
        only the body, so evidence stays readable.
        """
        return f"{self.title} - {self.section}\n{self.text}"

    def citation_line(self) -> str:
        return f"{self.title} - {self.section} ({self.source})"

    def as_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "section": self.section,
            "source": self.source,
            "start": self.start,
            "end": self.end,
            "preview": self.text[:120],
        }


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into ``(heading, body)`` pairs, dropping the leading title.

    A document with no headings becomes a single section named after its first
    line, so the chunker never has to special-case a heading-free file.
    """
    matches = list(HEADING.finditer(text))
    if not matches:
        first_line = text.strip().splitlines()[0] if text.strip() else "Document"
        return [("Overview", text.strip())]

    sections: list[tuple[str, str]] = []
    title = matches[0].group(2).strip()
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append(("Overview", preamble))

    for index, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if level == 1 and heading == title:
            # The document title itself is not a section body.
            if body:
                sections.append((title, body))
            continue
        if body:
            sections.append((heading, body))
    return sections or [("Overview", text.strip())]


def chunk_text(text: str, max_chars: int = 600, overlap: int = 80) -> list[tuple[str, int, int]]:
    """Split text into ``(chunk, start, end)`` triples on sentence boundaries.

    Sentences are packed until ``max_chars`` is reached, then the window restarts
    ``overlap`` characters back so a boundary-spanning fact appears twice.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be non-negative and smaller than max_chars")

    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [(text, 0, len(text))]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[tuple[str, int, int]] = []
    buffer: list[str] = []
    cursor = 0
    chunk_start = 0

    for sentence in sentences:
        if buffer and len(" ".join(buffer)) + len(sentence) + 1 > max_chars:
            joined = " ".join(buffer)
            chunks.append((joined, chunk_start, chunk_start + len(joined)))
            keep: list[str] = []
            keep_len = 0
            for previous in reversed(buffer):
                if keep_len + len(previous) > overlap:
                    break
                keep.insert(0, previous)
                keep_len += len(previous) + 1
            buffer = keep
            chunk_start = max(cursor - keep_len, chunk_start + 1)
        buffer.append(sentence)
        cursor += len(sentence) + 1

    if buffer:
        joined = " ".join(buffer)
        chunks.append((joined, chunk_start, chunk_start + len(joined)))
    return chunks


def load_documents(root: Path | str) -> list[Document]:
    """Load every supported file under ``root`` in a stable sorted order."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"corpus directory not found: {root}")

    documents: list[Document] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        sections = split_sections(text)
        title = sections[0][0] if sections else path.stem
        h1 = HEADING.search(text)
        if h1 and len(h1.group(1)) == 1:
            title = h1.group(2).strip()
        documents.append(
            Document(
                doc_id=path.stem,
                title=title,
                source=str(path.relative_to(root)).replace("\\", "/"),
                sections=tuple(sections),
            )
        )
    return documents


def build_chunks(
    documents: list[Document],
    max_chars: int = 600,
    overlap: int = 80,
) -> list[Chunk]:
    """Turn documents into chunks with stable, citable identifiers."""
    chunks: list[Chunk] = []
    for document in documents:
        for section_index, (heading, body) in enumerate(document.sections):
            for piece_index, (piece, start, end) in enumerate(chunk_text(body, max_chars, overlap)):
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.doc_id}#{slugify(heading)}#{piece_index}",
                        doc_id=document.doc_id,
                        title=document.title,
                        section=heading,
                        text=piece,
                        source=document.source,
                        start=start,
                        end=end,
                    )
                )
    return chunks


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens used by both retrieval and the offline model."""
    return WORD.findall(text.lower())
