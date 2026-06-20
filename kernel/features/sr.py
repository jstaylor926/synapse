"""Spaced repetition via FSRS-6 (py-fsrs). Stub.

Tracks study decay natively and schedules the next review for each card. Card
state is persisted in `data/db/sr.db`.
"""

from __future__ import annotations

from contracts.models import ReviewCard


def review(card: ReviewCard, rating: int) -> ReviewCard:
    """Apply an FSRS rating (1=again .. 4=easy) and return the updated card."""
    raise NotImplementedError
