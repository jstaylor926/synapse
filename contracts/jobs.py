"""Async job protocol (§4.6) — one generic protocol every async tool shares.

Submission is implicit: any async tool returns a ``JobSubmitResponse``; surfaces
then poll ``job_status`` until ``done``/``failed`` and list in-flight work with
``job_list``. States: queued → running → done | failed (+ best-effort cancelled).
"""
from typing import Any, List, Optional

from pydantic import BaseModel


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued | running | done | failed | cancelled
    progress: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class JobListItem(BaseModel):
    job_id: str
    kind: str
    status: str
    started: Optional[str] = None  # ISO datetime


class JobListResponse(BaseModel):
    jobs: List[JobListItem] = []


class JobCancelResponse(BaseModel):
    job_id: str
    cancelled: bool
