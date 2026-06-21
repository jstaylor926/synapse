"""Card + review-state store (§11) — SQLite, stdlib only.

FSRS review logs live in SQLite (the architecture's stated default; card
frontmatter is the alternative). The scheduler is separate (scheduler.py); this
module only persists.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import List, Optional

from .scheduler import CardState


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

    def add(self, deck: str, front: str, back: str, initial: CardState,
            card_id: Optional[str] = None) -> str:
        cid = card_id or str(uuid.uuid4())
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO cards (id,deck,front,back,due,stability,"
                "difficulty,reps,lapses,last_review,state) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (cid, deck, front, back, initial.due, initial.stability,
                 initial.difficulty, initial.reps, initial.lapses,
                 initial.last_review, initial.state),
            )
            self._db.commit()
        return cid

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

    def due(self, deck: Optional[str], on: Optional[str]) -> List[str]:
        cutoff = on or _dt.datetime.now().replace(microsecond=0).isoformat()
        if deck:
            rows = self._db.execute(
                "SELECT id FROM cards WHERE deck=? AND due<=? ORDER BY due",
                (deck, cutoff),
            ).fetchall()
        else:
            rows = self._db.execute(
                "SELECT id FROM cards WHERE due<=? ORDER BY due", (cutoff,)
            ).fetchall()
        return [r["id"] for r in rows]

    def stats(self, deck: Optional[str]) -> tuple[float, int]:
        """(mean recent retention proxy, due-soon load)."""
        where, params = ("WHERE deck=?", (deck,)) if deck else ("", ())
        rows = self._db.execute(f"SELECT reps,lapses,due FROM cards {where}", params).fetchall()
        if not rows:
            return 0.0, 0
        total_reps = sum(r["reps"] for r in rows)
        total_lapses = sum(r["lapses"] for r in rows)
        retention = 1.0 - (total_lapses / total_reps) if total_reps else 0.0
        horizon = (_dt.datetime.now() + _dt.timedelta(days=1)).replace(microsecond=0).isoformat()
        load = sum(1 for r in rows if r["due"] <= horizon)
        return round(retention, 3), load

    @staticmethod
    def _row_to_state(row: sqlite3.Row) -> CardState:
        return CardState(
            due=row["due"], stability=row["stability"], difficulty=row["difficulty"],
            reps=row["reps"], lapses=row["lapses"], last_review=row["last_review"],
            state=row["state"],
        )
