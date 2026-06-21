"""Pydantic models shared across the kernel edges.

Keep these in sync with `packages/contracts-ts/src/index.ts`. When this file
changes, regenerate the TypeScript mirror (see that package's README).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    """A single retrieval result."""

    doc_id: str
    title: str
    path: str = Field(description="Vault-relative Markdown path.")
    snippet: str
    score: float


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Job(BaseModel):
    """A unit of async work on the SQLite job queue."""

    id: str
    kind: str = Field(description="e.g. 'ingest_web', 'ingest_pdf', 'transcribe'.")
    payload: dict = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    error: str | None = None
    created_at: datetime | None = None


class Task(BaseModel):
    """A planner task tracked natively in the vault ontology."""

    id: str
    title: str
    done: bool = False
    due: datetime | None = None
    topic: str | None = None


class ReviewCard(BaseModel):
    """An FSRS-6 spaced-repetition card."""

    id: str
    front: str
    back: str
    due: datetime | None = None
    stability: float = 0.0
    difficulty: float = 0.0


class Citation(BaseModel):
    """A pointer back to a source chunk — one shape wherever a citation appears."""

    source: str
    score: float
    snippet: str


class ReasonAsk(BaseModel):
    """Request body for `reason_ask`."""

    question: str
    k: int = 8


class ReasonAnswer(BaseModel):
    """A grounded answer with citations back to source chunks (never fabricated)."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    # Present only for multi-step reasoning — the decomposed sub-questions.
    steps: list[str] | None = None
    # Which degradation rung produced this: "extractive" (no LLM) or "generative".
    mode: str = "extractive"
