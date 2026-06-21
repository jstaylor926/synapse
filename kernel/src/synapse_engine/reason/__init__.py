"""Reasoning over the knowledge base.

LLM-backed question answering grounded in retrieved vault context. When a model
is reachable (litellm → local Ollama by default, Anthropic when a key is
present) `answer()` returns a **generative** answer grounded in the retrieved
chunks. With no model it falls back to the **extractive floor** (§1.10, §12):
it never fabricates — the answer *is* the highest-ranked source chunks, returned
verbatim with citations. Both rungs share this signature, so callers never move.
"""

from __future__ import annotations

from contracts.models import Citation, ReasonAnswer

from synapse_engine.kb import search
from synapse_engine.llm import complete

_GROUNDED_SYSTEM = (
    "You are Synapse, a study assistant. Answer the user's question using ONLY the "
    "numbered context passages from their personal vault. Cite passages inline as "
    "[1], [2], etc. If the context does not cover the question, say so plainly "
    "rather than inventing facts. Be concise."
)


def citations_for(question: str, k: int) -> list[Citation]:
    """Retrieve the top-`k` chunks for `question` as `Citation`s (shared shape)."""
    return [
        Citation(source=f"{h.title} · {h.path}", score=h.score, snippet=h.snippet)
        for h in search(question, k=k)
    ]


def context_block(citations: list[Citation]) -> str:
    """Number the citations for a grounded prompt / extractive answer body."""
    return "\n\n".join(f"[{i}] {c.snippet}" for i, c in enumerate(citations, start=1))


def extractive_floor(citations: list[Citation]) -> ReasonAnswer:
    """The offline rung: the answer is the source text itself, never fabricated."""
    if not citations:
        return ReasonAnswer(
            answer=(
                "No matching notes in the vault yet. Ingest some material via "
                "Capture (kb_ingest / web_ingest), then ask again."
            ),
            citations=[],
            mode="extractive",
        )

    header = (
        "Grounded in your vault (extractive floor — no LLM reachable, so the "
        "answer is the source text itself, never fabricated):"
    )
    return ReasonAnswer(
        answer=f"{header}\n\n{context_block(citations)}",
        citations=citations,
        mode="extractive",
    )


def answer(question: str, k: int = 8) -> ReasonAnswer:
    """Answer `question` grounded in the top-`k` retrieved chunks.

    Generative when a model is reachable; extractive floor otherwise.
    """
    citations = citations_for(question, k=k)
    if citations:
        prompt = f"Context:\n{context_block(citations)}\n\nQuestion: {question}"
        text = complete(_GROUNDED_SYSTEM, prompt)
        if text:
            return ReasonAnswer(answer=text, citations=citations, mode="generative")
    return extractive_floor(citations)
