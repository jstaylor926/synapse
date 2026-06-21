"""Plain dataclasses shared across the engine (stdlib only)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Chunk:
    id: str
    text: str
    source: str            # origin path or note title
    metadata: dict[str, Any] = field(default_factory=dict)
    vector: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Citation:
    source: str
    score: float
    snippet: str


@dataclass
class Answer:
    question: str
    answer: str
    citations: list[Citation] = field(default_factory=list)

    def render(self) -> str:
        lines = [self.answer.strip(), ""]
        if self.citations:
            lines.append("Sources:")
            for c in self.citations:
                lines.append(f"  - {c.source}  (score {c.score:.2f})")
        return "\n".join(lines)


@dataclass
class Flashcard:
    front: str
    back: str
    source: str = ""


@dataclass
class QuizItem:
    question: str
    answer: str
    source: str = ""

    def is_correct(self, response: str) -> bool:
        return self.answer.strip().lower() in (response or "").strip().lower()
