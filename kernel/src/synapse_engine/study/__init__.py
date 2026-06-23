"""Study orchestration.

Surfaces spaced-repetition reviews (FSRS-6, implemented under `features/sr.py`)
as flashcards and walking-quizzes, and tracks study decay natively against the
vault's ontology.
"""

from __future__ import annotations

from contracts.models import ReviewCard

from synapse_engine.study.extract import extract

__all__ = ["due_cards", "extract"]


def due_cards(limit: int = 20) -> list[ReviewCard]:
    """Return cards due for review, ordered by urgency. Stub."""
    raise NotImplementedError
