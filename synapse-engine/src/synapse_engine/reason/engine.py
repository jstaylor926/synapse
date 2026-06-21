"""ReasoningEngine — retrieval-augmented Q&A with citations, plus a simple
multi-step decomposition hook (the 'personal reasoning engine' identity)."""
from __future__ import annotations

import re

from ..config import Config
from ..models import Answer
from .llm import get_llm
from .retriever import Retriever


class ReasoningEngine:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.retriever = Retriever(config)
        self.llm = get_llm(config)

    def ask(self, question: str, k: int | None = None) -> Answer:
        citations = self.retriever.citations(question, k)
        text = self.llm.answer(question, citations)
        return Answer(question=question, answer=text, citations=citations)

    def reason(self, question: str, k: int | None = None) -> Answer:
        """Decompose a multi-part question, retrieve per sub-question, then
        answer over the merged evidence. A deliberately small stand-in for a
        real planner — the seam where deeper reasoning plugs in."""
        subs = self._decompose(question)
        merged = []
        seen = set()
        for sub in subs:
            for c in self.retriever.citations(sub, k):
                key = (c.source, c.snippet[:60])
                if key not in seen:
                    seen.add(key)
                    merged.append(c)
        merged.sort(key=lambda c: c.score, reverse=True)
        merged = merged[: (k or self.config.top_k)]
        text = self.llm.answer(question, merged)
        if len(subs) > 1:
            text += "\n\nSub-questions considered: " + " | ".join(subs)
        return Answer(question=question, answer=text, citations=merged)

    @staticmethod
    def _decompose(question: str) -> list[str]:
        parts = re.split(r"\b(?:and|then|also|;|\?)\b", question)
        parts = [p.strip(" ?.") for p in parts if len(p.strip()) > 8]
        return parts or [question]
