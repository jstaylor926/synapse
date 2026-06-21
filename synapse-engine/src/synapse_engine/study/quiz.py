"""Quiz generation (fill-in-the-blank) + grading."""
from __future__ import annotations

from ..config import Config
from ..models import QuizItem
from ..reason.retriever import Retriever
from ._text import key_term, sentences


def make_quiz(config: Config, topic: str, n: int = 5) -> list[QuizItem]:
    retriever = Retriever(config)
    hits = retriever.retrieve(topic, k=max(n, config.top_k))
    items: list[QuizItem] = []
    for chunk, _ in hits:
        for sent in sentences(chunk.text):
            term = key_term(sent)
            if not term:
                continue
            blanked = sent.replace(term, "_____", 1)
            if "_____" in blanked:
                items.append(QuizItem(question=blanked, answer=term, source=chunk.source))
            if len(items) >= n:
                return items
    return items[:n]


def grade(items: list[QuizItem], responses: list[str]) -> dict:
    correct = sum(1 for it, r in zip(items, responses) if it.is_correct(r))
    return {"correct": correct, "total": len(items),
            "pct": round(100 * correct / len(items), 1) if items else 0.0}
