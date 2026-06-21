"""Code study buddy — answer coding questions grounded in YOUR ingested code,
docs, and notes (retrieval), rather than from the model's memory alone."""
from __future__ import annotations

from ..config import Config
from ..models import Answer
from ..reason.engine import ReasoningEngine


def assist(config: Config, query: str, k: int | None = None) -> Answer:
    engine = ReasoningEngine(config)
    ans = engine.ask(query, k)
    if not ans.citations:
        ans.answer = (
            "Nothing in your knowledge base matches that yet. Ingest the relevant "
            "code/docs (synapse ingest <path>) so answers stay grounded in your "
            "own material.\n\n" + ans.answer
        )
    return ans
