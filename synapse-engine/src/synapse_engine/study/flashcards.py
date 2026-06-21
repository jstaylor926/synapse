"""Flashcard generation from the knowledge base (heuristic by default)."""
from __future__ import annotations

from ..config import Config
from ..models import Flashcard
from ..reason.retriever import Retriever
from ._text import definition_pairs, sentences


def make_flashcards(config: Config, topic: str, n: int = 8) -> list[Flashcard]:
    retriever = Retriever(config)
    hits = retriever.retrieve(topic, k=max(n, config.top_k))
    cards: list[Flashcard] = []
    seen: set[str] = set()
    for chunk, _ in hits:
        for term, definition in definition_pairs(chunk.text):
            if term.lower() in seen:
                continue
            seen.add(term.lower())
            cards.append(Flashcard(front=f"What is {term}?", back=definition, source=chunk.source))
        for sent in sentences(chunk.text):
            if " is " in sent or " are " in sent or "refers to" in sent:
                head = sent.split(" is ")[0].split(" are ")[0].strip()
                if 3 < len(head) < 60 and head.lower() not in seen:
                    seen.add(head.lower())
                    cards.append(Flashcard(front=f"Define: {head}", back=sent, source=chunk.source))
        if len(cards) >= n:
            break
    return cards[:n]
