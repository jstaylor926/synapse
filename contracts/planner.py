"""Planner tool contracts (§4.5) — the orchestrator surface.

The planner *sequences and binds*; the work lives in the capabilities. These
models mirror the vault planning ontology (§9): an assignment decomposes into
tasks, each task maps to resources (`resources:`) and a tool (`binding:`), and
tasks are projected onto free time as study blocks.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Binding(BaseModel):
    """A task → feature-tool mapping (the `binding:` edge)."""
    tool: str
    args: Dict[str, Any] = {}


class Task(BaseModel):
    id: str
    title: Optional[str] = None
    assignment: Optional[str] = None
    topic: List[str] = []
    resources: List[str] = []  # the `resources:` edge
    binding: Optional[Binding] = None
    estimate: Optional[str] = None  # e.g. "45m"
    scheduled: Optional[str] = None  # ISO datetime
    status: str = "todo"


class Topic(BaseModel):
    id: str
    course: Optional[str] = None
    resources: List[str] = []


class Resource(BaseModel):
    id: str
    kind: str  # pdf | note | url | deck | transcript | mail
    source: str
    doc_id: Optional[str] = None  # link into the derived KB index


class ScheduledBlock(BaseModel):
    id: str
    when: str  # ISO datetime
    duration: str  # e.g. "45m"
    tasks: List[str] = []
    calendar_ref: Optional[str] = None  # read-only back-ref to busy/free source


class PlanBreakdownInput(BaseModel):
    assignment_ref: str


class PlanBreakdownOutput(BaseModel):
    tasks: List[Task] = []
    topics: List[Topic] = []
    resources: List[Resource] = []
    proposed_bindings: List[Binding] = []


class PlanScheduleInput(BaseModel):
    scope: str  # e.g. an assignment id, a course, or "all"
    horizon: str  # e.g. "2w"


class PlanScheduleOutput(BaseModel):
    scheduled_blocks: List[ScheduledBlock] = []


class PlanAgendaInput(BaseModel):
    date: Optional[str] = None  # ISO date; None ⇒ today


class PlanAgendaOutput(BaseModel):
    blocks: List[ScheduledBlock] = []
    tasks: List[Task] = []


class PlanBindInput(BaseModel):
    task_ref: str
    tool: str
    args: Dict[str, Any] = {}


class PlanBindOutput(BaseModel):
    binding_id: str


class PlanRunInput(BaseModel):
    task_ref: str


class PlanRunOutput(BaseModel):
    # Inherits the bound tool's sync/async shape: a result, or a job ticket.
    result: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


class PlanSyncExternalOutput(BaseModel):
    """Read-only pull from Google Calendar (§10). Never writes back."""
    pulled: int
    ics_url: Optional[str] = None  # optional one-way read-only feed
