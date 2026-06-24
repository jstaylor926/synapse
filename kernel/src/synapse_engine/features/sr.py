"""Spaced repetition (FSRS-6) — the review-loop engine.

Ported from the legacy tree (`features/sr/{scheduler,store,service}.py`) into the
canonical kernel as a single cohesive module. Three layers:

    scheduler  — pure interval math. SimpleScheduler is the dependency-free floor;
                 FsrsScheduler (py-fsrs, FSRS-6) is the opt-in upgrade. Same shape
                 as the llm.py seam: it degrades, it never blocks the core.
    store      — stdlib SQLite persistence at `settings.sr_db` (a derived index,
                 NOT the vault, so no gatekeeper is required to write it).
    service    — the typed public API the edges call (`add_cards`, `due_cards`,
                 `review`).

Card identity is a content hash of (deck, front, back): re-saving a generated
deck is idempotent and never resets a card's existing schedule.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import sqlite3
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Protocol

from contracts.models import Flashcard, ReviewCard

from synapse_engine.config import get_settings

# FSRS rating convention (1=Again … 4=Easy), shared with contracts.GradeRequest.
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


# --------------------------------------------------------------------------- #
# Scheduler — pure interval math, floor + FSRS-6 upgrade behind one Protocol
# --------------------------------------------------------------------------- #
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


@lru_cache(maxsize=1)
def get_scheduler() -> Scheduler:
    """SimpleScheduler by default; FSRS-6 when SYNAPSE_SR_SCHEDULER=fsrs."""
    if os.environ.get("SYNAPSE_SR_SCHEDULER", "simple").lower() == "fsrs":
        return FsrsScheduler()
    return SimpleScheduler()


# --------------------------------------------------------------------------- #
# Store — stdlib SQLite, one row per card (derived index at settings.sr_db)
# --------------------------------------------------------------------------- #
class SrStore:
    def __init__(self, db_path: Path) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._init()

    def _init(self) -> None:
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id    TEXT PRIMARY KEY,
                deck  TEXT NOT NULL,
                front TEXT NOT NULL,
                back  TEXT NOT NULL,
                due         TEXT NOT NULL,
                stability   REAL NOT NULL DEFAULT 0,
                difficulty  REAL NOT NULL DEFAULT 0,
                reps        INTEGER NOT NULL DEFAULT 0,
                lapses      INTEGER NOT NULL DEFAULT 0,
                last_review TEXT,
                state       TEXT NOT NULL DEFAULT 'new'
            )
            """
        )
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_cards_deck_due ON cards(deck, due)")
        self._db.commit()

    def add(self, card_id: str, deck: str, front: str, back: str, initial: CardState) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO cards (id,deck,front,back,due,stability,"
                "difficulty,reps,lapses,last_review,state) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (card_id, deck, front, back, initial.due, initial.stability,
                 initial.difficulty, initial.reps, initial.lapses,
                 initial.last_review, initial.state),
            )
            self._db.commit()

    def exists(self, card_id: str) -> bool:
        return self._db.execute("SELECT 1 FROM cards WHERE id=?", (card_id,)).fetchone() is not None

    def get_state(self, card_id: str) -> Optional[CardState]:
        row = self._db.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        return self._row_to_state(row) if row else None

    def update_state(self, card_id: str, state: CardState) -> None:
        with self._lock:
            self._db.execute(
                "UPDATE cards SET due=?,stability=?,difficulty=?,reps=?,lapses=?,"
                "last_review=?,state=? WHERE id=?",
                (state.due, state.stability, state.difficulty, state.reps,
                 state.lapses, state.last_review, state.state, card_id),
            )
            self._db.commit()

    def due_rows(self, deck: Optional[str], on: Optional[str], limit: int) -> list[sqlite3.Row]:
        cutoff = on or _iso(_now())
        if deck:
            return self._db.execute(
                "SELECT * FROM cards WHERE deck=? AND due<=? ORDER BY due LIMIT ?",
                (deck, cutoff, limit),
            ).fetchall()
        return self._db.execute(
            "SELECT * FROM cards WHERE due<=? ORDER BY due LIMIT ?", (cutoff, limit)
        ).fetchall()

    @staticmethod
    def _row_to_state(row: sqlite3.Row) -> CardState:
        return CardState(
            due=row["due"], stability=row["stability"], difficulty=row["difficulty"],
            reps=row["reps"], lapses=row["lapses"], last_review=row["last_review"],
            state=row["state"],
        )


@lru_cache(maxsize=1)
def _store() -> SrStore:
    return SrStore(get_settings().sr_db)


# --------------------------------------------------------------------------- #
# Service — the typed public API the edges call
# --------------------------------------------------------------------------- #
def _card_id(deck: str, front: str, back: str) -> str:
    """Stable content hash so re-saving a generated deck is idempotent."""
    raw = f"{deck}\x1f{front}\x1f{back}".encode()
    return hashlib.sha1(raw).hexdigest()[:16]


def add_cards(deck: str, cards: list[Flashcard]) -> list[str]:
    """Persist flashcards, returning their stable ids (input order).

    Idempotent: a card already in the store keeps its schedule untouched; only
    genuinely new cards are inserted with a fresh `new` state.
    """
    store, scheduler = _store(), get_scheduler()
    ids: list[str] = []
    for card in cards:
        cid = _card_id(deck, card.front, card.back)
        if not store.exists(cid):
            store.add(cid, deck, card.front, card.back, scheduler.new_state())
        ids.append(cid)
    return ids


def due_cards(limit: int = 20, deck: Optional[str] = None) -> list[ReviewCard]:
    """Cards due for review now, most-urgent first."""
    rows = _store().due_rows(deck, None, limit)
    return [
        ReviewCard(
            id=r["id"], front=r["front"], back=r["back"],
            due=_dt.datetime.fromisoformat(r["due"]),
            stability=r["stability"], difficulty=r["difficulty"],
        )
        for r in rows
    ]


def review(card_id: str, rating: int) -> CardState:
    """Apply a grade and persist the new schedule. Raises if the card is unknown."""
    store, scheduler = _store(), get_scheduler()
    state = store.get_state(card_id)
    if state is None:
        raise KeyError(card_id)
    new_state = scheduler.review(state, rating)
    store.update_state(card_id, new_state)
    return new_state
