"""Retriever — the hybrid query pipeline (§8) with graceful degradation (§12).

    query
      ├─ embed ─────────────► vector top-K  (sqlite-vec / cosine)
      ├─ tokenize ──────────► lexical top-K (FTS5 / BM25)
      ├─ merge → RRF ───────► candidate set (~candidate_k)
      ├─ cross-encoder rerank (bounded + timeout, inline) → top-N
      └─ citations back to source chunks

Degradation ladder, each step independent and self-healing:
  • embeddings model missing → lexical-only (RRF over the BM25 list)
  • lexical miss            → vector-only
  • reranker missing/slow   → RRF order
"""
from __future__ import annotations

from typing import List, Tuple

from ..config import Config
from ..kb.embeddings import get_embedder
from ..kb.rrf import reciprocal_rank_fusion
from ..kb.store import VectorStore
from ..models import Chunk, Citation
from .rerank import rerank


class Retriever:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.store = VectorStore(config.store_path)
        try:
            self.embedder = get_embedder(config)
        except Exception:
            self.embedder = None  # → lexical-only degradation (§12)

    def retrieve(self, query: str, k: int | None = None) -> List[Tuple[Chunk, float]]:
        k = k or self.config.top_k
        cand_k = max(self.config.candidate_k, k)

        ranked_lists: List[List[Tuple[Chunk, float]]] = []
        if self.embedder is not None:
            try:
                qv = self.embedder.embed(query)
                ranked_lists.append(self.store.vector_search(qv, cand_k))
            except Exception:
                pass  # vector half down → fall through to lexical
        ranked_lists.append(self.store.lexical_search(query, cand_k))

        candidates = reciprocal_rank_fusion([r for r in ranked_lists if r])
        if not candidates:
            return []

        if self.config.rerank_enabled:
            return rerank(
                query,
                candidates[: self.config.rerank_candidates],
                top_n=k,
                model_name=self.config.rerank_model,
                timeout=self.config.rerank_timeout,
            )
        return candidates[:k]

    def citations(self, query: str, k: int | None = None) -> List[Citation]:
        return [
            Citation(source=c.source, score=score, snippet=c.text[:240].strip())
            for c, score in self.retrieve(query, k)
            if score > 0
        ]
