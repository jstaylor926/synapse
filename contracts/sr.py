"""Spaced-repetition tool contracts (§4.3) — py-fsrs / FSRS-6.

Ratings follow the FSRS convention: 1=Again, 2=Hard, 3=Good, 4=Easy.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Card(BaseModel):
    id: Optional[str] = None  # assigned on add if absent
    front: str
    back: str
    deck: Optional[str] = None  # None ⇒ inherit the deck from SrAddInput


class SrAddInput(BaseModel):
    deck: str
    cards: List[Card]


class SrAddOutput(BaseModel):
    added: int


class SrDueInput(BaseModel):
    deck: Optional[str] = None
    on: Optional[str] = None  # ISO date; None ⇒ now


class SrDueOutput(BaseModel):
    due: List[str] = []  # card_ids


class SrReviewInput(BaseModel):
    card_id: str
    rating: int  # 1..4 (Again/Hard/Good/Easy)


class SrReviewOutput(BaseModel):
    next_due: str  # ISO datetime


class SrStatsInput(BaseModel):
    deck: Optional[str] = None


class SrStatsOutput(BaseModel):
    retention: float  # predicted retention 0..1
    load: int  # reviews due in the near horizon
