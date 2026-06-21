"""Chunking (§8) — respect structure, not arbitrary windows.

Prose is split on markdown headers so a chunk is a coherent section, and the
section's heading trail is prepended to each piece for retrieval context. Code is
chunked on function/class boundaries via tree-sitter (seam below). Both fall back
to character packing for oversized or unstructured input, so chunking never fails.
"""
from __future__ import annotations

import re

_HEADER = re.compile(r"^(#{1,6})\s+(.*)$")
_HAS_HEADER = re.compile(r"(?m)^#{1,6}\s+")  # multiline scan for header detection


def _pack_paragraphs(text: str, size: int, overlap: int) -> list[str]:
    """Original behavior: blank-line split, pack to ~size chars, stitch overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}" if buf else para
        else:
            if buf:
                chunks.append(buf)
            if len(para) <= size:
                buf = para
            else:
                start = 0
                while start < len(para):
                    chunks.append(para[start:start + size])
                    start += size - overlap
                buf = ""
    if buf:
        chunks.append(buf)
    if overlap and len(chunks) > 1:
        stitched = [chunks[0]]
        for prev, cur in zip(chunks, chunks[1:]):
            stitched.append((prev[-overlap:] + "\n\n" + cur).strip())
        return stitched
    return chunks


def _split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Split into (heading_trail, body) sections by markdown headers, tracking the
    nesting so each section carries its parent headings as context."""
    sections: list[tuple[str, str]] = []
    trail: list[str] = []  # (level, title) stack flattened to titles
    levels: list[int] = []
    body: list[str] = []

    def flush() -> None:
        text_body = "\n".join(body).strip()
        if text_body:
            sections.append((" > ".join(trail), text_body))

    for line in text.splitlines():
        m = _HEADER.match(line)
        if m:
            flush()
            body = []
            level = len(m.group(1))
            title = m.group(2).strip()
            while levels and levels[-1] >= level:
                levels.pop()
                trail.pop()
            levels.append(level)
            trail.append(title)
        else:
            body.append(line)
    flush()
    return sections


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    """Header-aware for markdown; char-packing otherwise. A section larger than
    ``size`` is packed within itself, keeping its heading trail as a prefix."""
    if not _HAS_HEADER.search(text):
        return _pack_paragraphs(text, size, overlap)

    chunks: list[str] = []
    for trail, body in _split_markdown_sections(text):
        prefix = f"{trail}\n\n" if trail else ""
        if len(prefix) + len(body) <= size:
            chunks.append((prefix + body).strip())
        else:
            for piece in _pack_paragraphs(body, size - len(prefix), overlap):
                chunks.append((prefix + piece).strip())
    return chunks or _pack_paragraphs(text, size, overlap)


def chunk_code(text: str, language: str, size: int = 800, overlap: int = 150) -> list[str]:
    """SEAM: split on function/class nodes via tree-sitter so a chunk is a whole
    definition. Falls back to char packing until grammars are wired (M1.6 tail).

        from tree_sitter_languages import get_parser
        tree = get_parser(language).parse(text.encode())
        # walk tree, emit one chunk per top-level function_definition / class
    """
    return _pack_paragraphs(text, size, overlap)
