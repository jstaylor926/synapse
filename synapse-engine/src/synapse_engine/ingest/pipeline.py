"""Ingestion pipeline: load -> chunk -> embed -> store, and mirror a source
note into the markdown vault (the source of truth)."""
from __future__ import annotations

import hashlib
from pathlib import Path

from ..config import Config
from ..kb.embeddings import get_embedder
from ..kb.store import VectorStore
from ..kb.vault import write_note
from ..models import Chunk
from .chunk import chunk_text
from .loaders import iter_source_files, load_text


def _chunk_id(source: str, idx: int, text: str) -> str:
    h = hashlib.sha1(f"{source}:{idx}:{text}".encode()).hexdigest()[:12]
    return f"{Path(source).stem}-{idx}-{h}"


def ingest_markdown_text(
    markdown: str, *, source: str, kind: str, config: Config,
    write_vault: bool = True,
) -> str:
    """Ingest already-extracted text (from a worker: PDF parse, transcript, web).

    Chunks → embeds → stores, mirrors a readable note into the vault via the
    gatekeeper, and returns a ``doc_id``. The async handlers land here so every
    heavy ingest shares one path.
    """
    embedder = get_embedder(config)
    store = VectorStore(config.store_path)
    title = Path(source).stem or "ingested"
    meta = {"kind": kind, "source": source}
    chunks = [
        Chunk(
            id=_chunk_id(source, i, piece),
            text=piece,
            source=source,
            metadata=meta,
            vector=embedder.embed(piece),
        )
        for i, piece in enumerate(chunk_text(markdown))
    ]
    store.add(chunks)
    if write_vault:
        write_note(config.vault_dir, title=title, body=markdown,
                   frontmatter={"source": source, "kind": kind})
    # doc_id keys into the derived index by source stem (stable, rebuildable).
    return f"kb:{Path(source).stem}"


def ingest_path(path: Path, config: Config, *, write_vault: bool = True) -> dict:
    embedder = get_embedder(config)
    store = VectorStore(config.store_path)
    files = iter_source_files(Path(path))
    if not files:
        return {"files": 0, "chunks_added": 0, "sources": []}

    added = 0
    sources: list[str] = []
    for file in files:
        text, meta = load_text(file)
        source = str(file)
        pieces = chunk_text(text)
        chunks = [
            Chunk(
                id=_chunk_id(source, i, piece),
                text=piece,
                source=source,
                metadata=meta,
                vector=embedder.embed(piece),
            )
            for i, piece in enumerate(pieces)
        ]
        added += store.add(chunks)
        sources.append(source)
        if write_vault and meta.get("kind") == "pdf":
            # keep a readable markdown mirror of binary sources in the vault
            write_note(
                config.vault_dir,
                title=file.stem,
                body=text,
                frontmatter={"source": source, "kind": meta.get("kind"),
                             "pages": meta.get("pages", "")},
            )
    return {"files": len(files), "chunks_added": added, "sources": sources}
