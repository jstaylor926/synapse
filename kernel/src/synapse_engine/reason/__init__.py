"""Reasoning over the knowledge base.

LLM-backed question answering grounded in retrieved vault context. The richer
path routes through litellm (local Ollama by default, Anthropic when a key is
present). Until that's wired, `answer()` runs the **extractive floor** (§1.10,
§12): with no LLM it never fabricates — the answer *is* the highest-ranked
source chunks, returned verbatim with citations. Both paths share this
signature.
"""

from __future__ import annotations

from contracts.models import Citation, ReasonAnswer

from synapse_engine.kb import search


def answer(question: str, k: int = 8) -> ReasonAnswer:
    """Answer `question` grounded in the top-`k` retrieved chunks."""
    hits = search(question, k=k)
    citations = [
        Citation(source=f"{h.title} · {h.path}", score=h.score, snippet=h.snippet)
        for h in hits
    ]

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
        "Grounded in your vault (extractive floor — no LLM configured, so the "
        "answer is the source text itself, never fabricated):"
    )
    body = "\n\n".join(f"[{i}] {c.snippet}" for i, c in enumerate(citations, start=1))

    return ReasonAnswer(answer=f"{header}\n\n{body}", citations=citations, mode="extractive")
