"""Hybrid retrieval over the vault.

The richer design fuses lexical (BM25 via SQLite FTS5) and semantic (vector
cosine via sqlite-vec) results with Reciprocal Rank Fusion, optionally reranked
by a cross-encoder. Until that index is built, `search()` runs the **offline
floor** (§12): a dependency-free BM25 scan over the Markdown vault. Both paths
share this signature, so callers never move when the index lands.
"""

from __future__ import annotations

import hashlib
import math
import re

from contracts.models import SearchHit

from synapse_engine.config import get_settings

_TOKEN = re.compile(r"[a-z0-9]+")
_HEADING = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_PARAGRAPH = re.compile(r"\n\s*\n")

# Okapi BM25 parameters — standard defaults.
_BM25_K1 = 1.5
_BM25_B = 0.75
_SNIPPET_CHARS = 280


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _title_for(rel_path: str, text: str) -> str:
    """First Markdown H1, else the filename stem."""
    m = _HEADING.search(text)
    if m:
        return m.group(1).strip()
    stem = rel_path.rsplit("/", 1)[-1]
    return stem[:-3] if stem.endswith(".md") else stem


def _snippet(text: str) -> str:
    flat = " ".join(text.split())
    if len(flat) <= _SNIPPET_CHARS:
        return flat
    return flat[: _SNIPPET_CHARS - 1].rstrip() + "…"


class _Chunk:
    __slots__ = ("doc_id", "title", "path", "text", "length", "tf")

    def __init__(self, doc_id: str, title: str, path: str, text: str, tokens: list[str]) -> None:
        self.doc_id = doc_id
        self.title = title
        self.path = path
        self.text = text
        self.length = len(tokens)
        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1
        self.tf = tf


def _collect_chunks() -> list[_Chunk]:
    """Read every Markdown file in the vault and split it into paragraph chunks."""
    vault = get_settings().vault_dir
    if not vault.exists():
        return []

    chunks: list[_Chunk] = []
    for md in sorted(vault.rglob("*.md")):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = md.relative_to(vault).as_posix()
        title = _title_for(rel, raw)
        for idx, para in enumerate(p.strip() for p in _PARAGRAPH.split(raw)):
            tokens = _tokenize(para)
            if not tokens:
                continue
            cid = f"{rel}#{idx}"
            doc_id = "kb:" + hashlib.sha1(cid.encode("utf-8")).hexdigest()[:12]
            chunks.append(_Chunk(doc_id, title, rel, para, tokens))
    return chunks


def search(query: str, k: int = 8) -> list[SearchHit]:
    """Return the top-`k` vault chunks for `query` (BM25 over the Markdown vault).

    Degrades cleanly: an empty/absent vault or an all-stopword query returns
    `[]` rather than raising, so surfaces always get an answer they can render.
    """
    q_terms = _tokenize(query)
    if not q_terms:
        return []

    chunks = _collect_chunks()
    if not chunks:
        return []

    n = len(chunks)
    avgdl = sum(c.length for c in chunks) / n
    q_unique = set(q_terms)
    df = {term: sum(1 for c in chunks if term in c.tf) for term in q_unique}
    idf = {
        term: math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
        for term in q_unique
        if df[term]
    }
    if not idf:
        return []

    scored: list[tuple[float, _Chunk]] = []
    for c in chunks:
        score = 0.0
        for term, term_idf in idf.items():
            tf = c.tf.get(term, 0)
            if not tf:
                continue
            denom = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * c.length / avgdl)
            score += term_idf * (tf * (_BM25_K1 + 1)) / denom
        if score > 0:
            scored.append((score, c))

    if not scored:
        return []
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = scored[:k]
    max_score = top[0][0] or 1.0
    return [
        SearchHit(
            doc_id=c.doc_id,
            title=c.title,
            path=c.path,
            snippet=_snippet(c.text),
            score=round(score / max_score, 4),
        )
        for score, c in top
    ]


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Standard RRF: score(d) = sum over rankings of 1 / (k + rank(d))."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores
