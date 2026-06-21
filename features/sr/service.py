"""Spaced-repetition service (§4.3) — typed in-process API over store + scheduler.

The MCP boundary is a thin adapter over these functions; both validate against
the same ``contracts.sr`` models (§13).
"""
from __future__ import annotations

from functools import lru_cache

from contracts.sr import (
    SrAddInput,
    SrAddOutput,
    SrDueInput,
    SrDueOutput,
    SrReviewInput,
    SrReviewOutput,
    SrStatsInput,
    SrStatsOutput,
)

from .. import data_dir
from .scheduler import get_scheduler
from .store import SrStore


@lru_cache(maxsize=1)
def _store() -> SrStore:
    return SrStore(data_dir() / "sr.db")


def sr_add(inp: SrAddInput) -> SrAddOutput:
    store, scheduler = _store(), get_scheduler()
    added = 0
    for card in inp.cards:
        store.add(
            deck=card.deck or inp.deck,
            front=card.front,
            back=card.back,
            initial=scheduler.new_state(),
            card_id=card.id,
        )
        added += 1
    return SrAddOutput(added=added)


def sr_due(inp: SrDueInput) -> SrDueOutput:
    return SrDueOutput(due=_store().due(inp.deck, inp.on))


def sr_review(inp: SrReviewInput) -> SrReviewOutput:
    store, scheduler = _store(), get_scheduler()
    state = store.get_state(inp.card_id)
    if state is None:
        raise ValueError(f"unknown card_id={inp.card_id!r}")
    new_state = scheduler.review(state, inp.rating)
    store.update_state(inp.card_id, new_state)
    return SrReviewOutput(next_due=new_state.due)


def sr_stats(inp: SrStatsInput) -> SrStatsOutput:
    retention, load = _store().stats(inp.deck)
    return SrStatsOutput(retention=retention, load=load)
