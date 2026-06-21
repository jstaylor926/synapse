"""Reciprocal Rank Fusion (§8) — merge ranked lists by position, not by score.

RRF is score-scale-agnostic: it combines a vector ranking and a lexical (BM25)
ranking using only each item's *rank*, so we never have to reconcile cosine
similarities with BM25 magnitudes. score(d) = Σ 1/(k + rank_i(d)).

Degenerate cases fall out naturally: with one input list, RRF preserves that
list's order — which is exactly the §12 degradation (no embeddings → BM25 order;
no lexical hits → vector order).
"""
from __future__ import annotations

from typing import List, Tuple

from ..models import Chunk

RRF_K = 60  # standard constant; dampens the contribution of low ranks


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[Chunk, float]]],
    *,
    k: int = RRF_K,
) -> List[Tuple[Chunk, float]]:
    """Fuse ranked (Chunk, score) lists into one, deduping by chunk id."""
    fused: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}
    for ranked in ranked_lists:
        for rank, (chunk, _score) in enumerate(ranked):
            fused[chunk.id] = fused.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)
            chunks.setdefault(chunk.id, chunk)
    merged = [(chunks[cid], score) for cid, score in fused.items()]
    merged.sort(key=lambda t: t[1], reverse=True)
    return merged
