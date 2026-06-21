"""Cheat sheet: compact the most relevant material into a one-glance summary."""
from __future__ import annotations

from ..config import Config
from ..reason.retriever import Retriever
from ._text import definition_pairs, sentences


def make_cheatsheet(config: Config, topic: str, max_points: int = 12) -> str:
    retriever = Retriever(config)
    hits = retriever.retrieve(topic, k=config.top_k)
    points: list[str] = []
    seen: set[str] = set()
    for chunk, _ in hits:
        for term, definition in definition_pairs(chunk.text):
            line = f"- **{term}** — {definition}"
            if term.lower() not in seen:
                seen.add(term.lower())
                points.append(line)
        for sent in sentences(chunk.text)[:2]:
            if sent[:40] not in seen:
                seen.add(sent[:40])
                points.append(f"- {sent}")
        if len(points) >= max_points:
            break
    body = "\n".join(points[:max_points]) or "- (no material found — ingest sources first)"
    return f"# Cheat sheet: {topic}\n\n{body}\n"
