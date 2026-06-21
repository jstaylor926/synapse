"""Cross-encoder reranking (§8) — inline, bounded, optional.

Reranking runs in the *synchronous query path* (not the job queue): a query that
returned a job ticket would break the interactive feel of asking a question. To
keep it interactive (target p95 ≲ 2 s) it is bounded two ways:

1. **Capped candidate set** — only the top RRF candidates are scored (the cap is
   what bounds CPU latency).
2. **Hard timeout** — scoring runs under a deadline; on timeout we return the
   RRF order unchanged.

It is also fully optional: if no cross-encoder model is available, we skip
reranking and return the RRF order (§12). The query always returns within budget.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import List, Tuple

from ..models import Chunk


def _load_cross_encoder(model_name: str):
    """Return a callable scoring [(query, passage)] → [float], or raise.

    Tries fastembed first (the locked embedding stack), then sentence-transformers.
    Lazy so the import cost is paid only when reranking is actually enabled.
    """
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        model = TextCrossEncoder(model_name=model_name)
        return lambda query, passages: list(model.rerank(query, passages))
    except Exception:
        pass
    from sentence_transformers import CrossEncoder  # may raise ImportError

    model = CrossEncoder(model_name)
    return lambda query, passages: [
        float(s) for s in model.predict([(query, p) for p in passages])
    ]


def rerank(
    query: str,
    candidates: List[Tuple[Chunk, float]],
    *,
    top_n: int,
    model_name: str,
    timeout: float,
) -> List[Tuple[Chunk, float]]:
    """Rerank a *capped* candidate set; fall back to RRF order on any failure."""
    if not candidates:
        return []
    try:
        scorer = _load_cross_encoder(model_name)
    except Exception:
        return candidates[:top_n]  # no model → RRF order (§12)

    passages = [c.text for c, _ in candidates]

    def _score():
        return scorer(query, passages)

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            scores = pool.submit(_score).result(timeout=timeout)
    except (FuturesTimeout, Exception):
        return candidates[:top_n]  # over budget or model error → RRF order

    ranked = sorted(
        zip((c for c, _ in candidates), scores),
        key=lambda t: t[1], reverse=True,
    )
    return [(chunk, float(score)) for chunk, score in ranked][:top_n]
