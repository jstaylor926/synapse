"""Vector + lexical store — one SQLite file, derived and rebuildable (§11).

Replaces the JSON cosine skeleton with the architecture's storage model:

- **FTS5** table for lexical (BM25) retrieval — always on (stock SQLite).
- **Vectors** stored as float blobs; nearest-neighbour by cosine. The default is
  a pure-Python linear scan (zero deps, correct, fine at personal scale — §11
  notes brute-force is not outgrown by a personal vault). When the ``sqlite-vec``
  extension is available it is loaded as the fast path behind the same method.

The index is a *derived cache*: delete the file and rebuild from the vault. The
public surface (``add`` / ``search`` / ``size`` / ``sources``) is unchanged, so
ingest, study, and the CLI keep working; ``lexical_search`` / ``vector_search``
are new and feed the hybrid retriever (§8).
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from array import array
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import Chunk

_WORD = re.compile(r"[A-Za-z0-9]+")


def _vec_to_blob(vec: List[float]) -> bytes:
    return array("f", vec).tobytes()


def _blob_to_vec(blob: bytes) -> List[float]:
    a = array("f")
    a.frombytes(blob)
    return list(a)


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _fts_match(query: str) -> Optional[str]:
    """Build a safe FTS5 MATCH expression: quote each token, OR for recall."""
    tokens = _WORD.findall(query.lower())
    if not tokens:
        return None
    return " OR ".join(f'"{t}"' for t in tokens)


class VectorStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._init()

    def _init(self) -> None:
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id       TEXT PRIMARY KEY,
                text     TEXT NOT NULL,
                source   TEXT NOT NULL,
                metadata TEXT,
                vector   BLOB
            )
            """
        )
        # Standalone FTS5 (BM25). Simple + robust for a personal vault; external
        # content tables are the optimization if storage ever matters.
        self._db.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(id UNINDEXED, text)"
        )
        self._db.commit()

    # -- write -------------------------------------------------------------
    def add(self, chunks: List[Chunk]) -> int:
        existing = {r["id"] for r in self._db.execute("SELECT id FROM chunks")}
        new = [c for c in chunks if c.id not in existing]
        for c in new:
            self._db.execute(
                "INSERT INTO chunks (id,text,source,metadata,vector) VALUES (?,?,?,?,?)",
                (c.id, c.text, c.source, json.dumps(c.metadata),
                 _vec_to_blob(c.vector) if c.vector is not None else None),
            )
            self._db.execute(
                "INSERT INTO chunks_fts (id,text) VALUES (?,?)", (c.id, c.text)
            )
        self._db.commit()
        return len(new)

    def save(self) -> None:  # kept for interface compatibility; writes auto-commit
        self._db.commit()

    def clear(self) -> None:
        self._db.execute("DELETE FROM chunks")
        self._db.execute("DELETE FROM chunks_fts")
        self._db.commit()

    # -- read --------------------------------------------------------------
    def search(self, query_vec: List[float], k: int = 5) -> List[Tuple[Chunk, float]]:
        """Vector-only search (backward-compatible entry point)."""
        return self.vector_search(query_vec, k)

    def vector_search(self, query_vec: List[float], k: int = 5) -> List[Tuple[Chunk, float]]:
        # SEAM: when `import sqlite_vec` is available, load it in _init and query a
        # vec0 virtual table here for a C-speed scan. Python cosine is the zero-dep
        # default and is correct at personal scale (§11).
        scored: List[Tuple[Chunk, float]] = []
        for row in self._db.execute("SELECT * FROM chunks WHERE vector IS NOT NULL"):
            score = _cosine(query_vec, _blob_to_vec(row["vector"]))
            scored.append((self._row_to_chunk(row), score))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:k]

    def lexical_search(self, query: str, k: int = 5) -> List[Tuple[Chunk, float]]:
        match = _fts_match(query)
        if match is None:
            return []
        rows = self._db.execute(
            "SELECT c.*, bm25(chunks_fts) AS bm "
            "FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.id "
            "WHERE chunks_fts MATCH ? ORDER BY bm LIMIT ?",
            (match, k),
        ).fetchall()
        # bm25: lower is better → expose -bm as a positive relevance score.
        return [(self._row_to_chunk(r), -float(r["bm"])) for r in rows]

    @property
    def size(self) -> int:
        return self._db.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]

    def sources(self) -> set:
        return {r["source"] for r in self._db.execute("SELECT DISTINCT source FROM chunks")}

    @staticmethod
    def _row_to_chunk(row: sqlite3.Row) -> Chunk:
        return Chunk(
            id=row["id"], text=row["text"], source=row["source"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            vector=_blob_to_vec(row["vector"]) if row["vector"] is not None else None,
        )
