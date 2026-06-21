"""Review schedulers — a pluggable seam, FSRS-first with an offline floor.

``FsrsScheduler`` (py-fsrs, FSRS-6) is the quality path the architecture locks.
``SimpleScheduler`` is the dependency-free floor so review works on a fresh clone
with no extra install — the same "degrade gracefully, never block the core"
philosophy as the extractive answerer. Pick via ``SYNAPSE_SR_SCHEDULER``.
"""
from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass
from typing import Optional, Protocol

# FSRS rating convention (shared with contracts.sr).
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


@dataclass
class CardState:
    """Scheduler-agnostic review state persisted per card."""
    due: str  # ISO datetime
    stability: float = 0.0
    difficulty: float = 0.0
    reps: int = 0
    lapses: int = 0
    last_review: Optional[str] = None
    state: str = "new"  # new | learning | review | relearning


def _now() -> _dt.datetime:
    return _dt.datetime.now()


def _iso(dt: _dt.datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


class Scheduler(Protocol):
    def new_state(self) -> CardState: ...
    def review(self, state: CardState, rating: int) -> CardState: ...


class SimpleScheduler:
    """Deterministic interval ladder — the offline floor (not FSRS, but honest).

    Again → 10m · Hard → ×1.2 · Good → ×2.5 · Easy → ×4, off a 1-day base.
    """

    _BASE_DAYS = 1.0
    _MULT = {HARD: 1.2, GOOD: 2.5, EASY: 4.0}

    def new_state(self) -> CardState:
        return CardState(due=_iso(_now()), state="new")

    def review(self, state: CardState, rating: int) -> CardState:
        now = _now()
        reps = state.reps + 1
        lapses = state.lapses + (1 if rating == AGAIN else 0)
        if rating == AGAIN:
            due = now + _dt.timedelta(minutes=10)
            new_state = "relearning"
            stability = max(self._BASE_DAYS, state.stability * 0.5)
        else:
            prev = state.stability or self._BASE_DAYS
            stability = prev * self._MULT[rating]
            due = now + _dt.timedelta(days=stability)
            new_state = "review"
        return CardState(
            due=_iso(due), stability=stability, difficulty=state.difficulty,
            reps=reps, lapses=lapses, last_review=_iso(now), state=new_state,
        )


class FsrsScheduler:  # pragma: no cover - exercised only when py-fsrs installed
    """FSRS-6 via py-fsrs. Maps our CardState ↔ the library's Card object."""

    def __init__(self) -> None:
        try:
            from fsrs import Scheduler as _FSRS  # py-fsrs
        except ImportError as exc:
            raise RuntimeError("FsrsScheduler needs py-fsrs (pip install fsrs)") from exc
        self._fsrs = _FSRS()

    def new_state(self) -> CardState:
        from fsrs import Card

        card = Card()
        return CardState(due=_iso(card.due), state="new")

    def review(self, state: CardState, rating: int) -> CardState:
        from fsrs import Card, Rating

        # Rehydrate a minimal Card from our persisted state.
        card = Card()
        if state.stability:
            card.stability = state.stability
        if state.difficulty:
            card.difficulty = state.difficulty
        card, _log = self._fsrs.review_card(card, Rating(rating))
        return CardState(
            due=_iso(card.due), stability=card.stability or 0.0,
            difficulty=card.difficulty or 0.0, reps=state.reps + 1,
            lapses=state.lapses + (1 if rating == AGAIN else 0),
            last_review=_iso(_now()), state="review",
        )


def get_scheduler() -> Scheduler:
    choice = os.environ.get("SYNAPSE_SR_SCHEDULER", "simple").lower()
    if choice == "fsrs":
        return FsrsScheduler()
    return SimpleScheduler()
