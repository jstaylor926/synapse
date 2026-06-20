"""Hybrid retrieval over the vault.

Fuses lexical (BM25 via SQLite FTS5) and semantic (vector cosine via
sqlite-vec) results with Reciprocal Rank Fusion, optionally reranked by a
cross-encoder. The index lives in `data/db/index.db` and is fully rebuildable
from the Markdown vault.
"""

from __future__ import annotations

from contracts.models import SearchHit


def search(query: str, k: int = 8) -> list[SearchHit]:
    """Return the top-`k` hits for `query`.

    Stub. The real implementation will:
      1. Run an FTS5 MATCH query for the lexical ranking.
      2. Embed the query and run a sqlite-vec KNN for the semantic ranking.
      3. Fuse both rankings with RRF (and optionally rerank).
    """
    raise NotImplementedError("Retrieval index not built yet — see docs/architecture.")


def reciprocal_rank_fusion(
    rankings: list[list[str]], k: int = 60
) -> dict[str, float]:
    """Standard RRF: score(d) = sum over rankings of 1 / (k + rank(d))."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores
