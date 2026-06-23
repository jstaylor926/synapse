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


class StudyKind(str, Enum):
    """The shape of study artifact `study_extract` should produce."""

    FLASHCARDS = "flashcards"
    QUIZ = "quiz"
    INTERVIEW = "interview"
    SUMMARY = "summary"


class Flashcard(BaseModel):
    """A front/back recall pair. Front is the prompt, back is the answer."""

    front: str
    back: str
    source: str | None = Field(default=None, description="Vault path/title it came from.")


class QuizItem(BaseModel):
    """A multiple-choice question. `options` includes the correct answer."""

    question: str
    options: list[str]
    answer_index: int = Field(description="Index into `options` of the correct answer.")
    source: str | None = None


class STARPrompt(BaseModel):
    """An interview prompt with a STAR-structured model answer."""

    prompt: str
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    source: str | None = None


class KeyPoint(BaseModel):
    """A single bulleted takeaway from the source material."""

    point: str
    source: str | None = None


class ExtractRequest(BaseModel):
    """Request body for `study_extract` — turn vault material into study artifacts."""

    topic: str = Field(description="Topic/query used to retrieve source chunks from the vault.")
    kind: StudyKind = StudyKind.FLASHCARDS
    n: int = Field(default=8, description="How many items to produce.")
    k: int = Field(default=8, description="How many vault chunks to retrieve as source.")


class ExtractResult(BaseModel):
    """Study artifacts extracted from the vault. Exactly one list is populated,
    matching `kind`. Grounded in `citations`; `mode` records the degradation rung
    ("generative" when a model answered, "extractive" for the never-fabricate floor).
    """

    kind: StudyKind
    flashcards: list[Flashcard] = Field(default_factory=list)
    quiz: list[QuizItem] = Field(default_factory=list)
    interview: list[STARPrompt] = Field(default_factory=list)
    key_points: list[KeyPoint] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    mode: str = "extractive"


class ReasonAnswer(BaseModel):
    """A grounded answer with citations back to source chunks (never fabricated)."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    # Present only for multi-step reasoning — the decomposed sub-questions.
    steps: list[str] | None = None
    # Which degradation rung produced this: "extractive" (no LLM) or "generative".
    mode: str = "extractive"
