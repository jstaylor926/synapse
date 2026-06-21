"""Knowledge-base tool contracts (§4.1).

Typed I/O for `kb_ingest` / `kb_search`. The MCP boundary validates external
input into these models; internal callers import the *same* models, so the
external contract and the in-process interface cannot drift (§13).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class KbIngestInput(BaseModel):
    path: str


class KbIngestResult(BaseModel):
    # Sync result (native/light ingest)…
    files: int = 0
    chunks_added: int = 0
    sources: List[str] = []
    doc_id: Optional[str] = None
    # …or, when a heavy parse is routed to the queue, just the ticket.
    job_id: Optional[str] = None


class KbSearchInput(BaseModel):
    query: str
    k: int = 5


class Hit(BaseModel):
    text: str
    source: str
    score: float


class KbSearchOutput(BaseModel):
    hits: List[Hit] = []
