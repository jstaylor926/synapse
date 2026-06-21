"""Shared contract spine (§4, §13).

One pydantic package, imported by *both* the MCP boundary and the in-process
call sites, so the external tool contract and the internal typed interface can
never drift apart. Submodules mirror the §4 tool catalog.

    from contracts import kb, reason, study, sr, capture, planner, pdf, jobs
    from contracts.reason import Citation, ReasonAnswer
"""
from __future__ import annotations

from . import capture, jobs, kb, pdf, planner, reason, sr, study

# Commonly-reached models, re-exported for convenience.
from .jobs import JobStatusResponse, JobSubmitResponse
from .reason import Citation, ReasonAnswer

__all__ = [
    "capture",
    "jobs",
    "kb",
    "pdf",
    "planner",
    "reason",
    "sr",
    "study",
    "Citation",
    "ReasonAnswer",
    "JobStatusResponse",
    "JobSubmitResponse",
]
