"""Code study buddy — answer coding questions grounded in YOUR ingested code,
docs, and notes (retrieval), never from the model's memory alone.

Generative when a model is reachable (returns corrected/reference code in fenced
blocks); otherwise it degrades to the same never-fabricate extractive floor as
`reason`, with a code-flavoured nudge. Read-only — it never writes the vault and
never executes code.
"""

from __future__ import annotations

from contracts.models import ReasonAnswer

from synapse_engine.llm import complete
from synapse_engine.reason import citations_for, context_block, extractive_floor

_CODE_SYSTEM = (
    "You are Code Buddy, a coding study assistant for a student's assignment. Use the "
    "numbered context passages from their vault when relevant and cite them inline as "
    "[1], [2]. Explain concisely what is wrong and why, then give corrected or reference "
    "code inside fenced ```python code blocks (use the right language tag). You reason "
    "about code but NEVER execute it — never claim to have run it or produced output."
)


def assist(query: str, k: int = 8) -> ReasonAnswer:
    """Grounded coding help over the vault's ingested code + docs."""
    citations = citations_for(query, k=k)
    context = (
        context_block(citations) if citations else "(no matching material in the knowledge base)"
    )

    text = complete(_CODE_SYSTEM, f"Context:\n{context}\n\n{query}")
    if text:
        return ReasonAnswer(answer=text, citations=citations, mode="generative")

    # No model reachable → never fabricate. Show the floor, nudge if nothing matched.
    floor = extractive_floor(citations)
    if not citations:
        floor.answer = (
            "Nothing in your knowledge base matches that yet, and no model is reachable "
            "to reason from scratch. Ingest the relevant code/docs, or start a local "
            "model (Ollama), then ask again.\n\n"
        ) + floor.answer
    return floor
