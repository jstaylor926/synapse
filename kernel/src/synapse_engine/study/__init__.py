"""Study orchestration.

Two halves of the study loop:

  - `extract()` turns vault material into study artifacts (flashcards, quiz,
    STAR, summary) — generative when a model is reachable, extractive floor
    otherwise. The AR glasses consume this to build a deck.
  - `save_flashcards()` / `due_cards()` / `grade()` close the *review* loop over
    the FSRS-6 store (`features.sr`): persist a deck, surface what's due, and
    schedule the next review from a tap on the glasses. State lives in the
    derived `sr.db`, so no vault gatekeeper is needed.
"""

from __future__ import annotations

import datetime as _dt

from contracts.models import Flashcard, GradeResult, ReviewCard

from synapse_engine.features import sr
from synapse_engine.study.extract import extract

__all__ = ["due_cards", "extract", "grade", "save_flashcards"]


def save_flashcards(deck: str, cards: list[Flashcard]) -> list[str]:
    """Persist a generated deck into the SR store; returns stable card ids."""
    return sr.add_cards(deck, cards)


def due_cards(limit: int = 20, deck: str | None = None) -> list[ReviewCard]:
    """Return cards due for review, ordered by urgency."""
    return sr.due_cards(limit=limit, deck=deck)


def grade(card_id: str, rating: int) -> GradeResult:
    """Apply an FSRS grade (1=Again..4=Easy) and report the next review."""
    state = sr.review(card_id, rating)
    next_due = _dt.datetime.fromisoformat(state.due)
    return GradeResult(
        card_id=card_id,
        next_due=next_due,
        interval=_humanize(next_due - _dt.datetime.now()),
        state=state.state,
    )


def _humanize(delta: _dt.timedelta) -> str:
    """A compact 'time until' label for the HUD: '10m', '3h', '2d', '5w'.

    Rounds to the nearest unit so a ~4-day interval reads '4d', not a floored
    '3d' (the few seconds spent computing the grade shouldn't bend the label).
    """
    secs = max(0, int(delta.total_seconds()))
    if secs < 3600:
        return f"{max(1, round(secs / 60))}m"
    if secs < 86400:
        return f"{max(1, round(secs / 3600))}h"
    days = round(secs / 86400)
    return f"{days}d" if days < 14 else f"{round(days / 7)}w"
