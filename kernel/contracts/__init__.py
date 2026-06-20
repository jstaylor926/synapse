"""Shared Pydantic contracts.

These models are the single source of truth for data crossing the kernel's
edges. They are mirrored into TypeScript under `packages/contracts-ts/` so every
surface (cockpit, glasses, CLI, extensions) stays in lockstep with the backend.
"""

from contracts.models import (
    Job,
    JobStatus,
    ReviewCard,
    SearchHit,
    Task,
)

__all__ = ["Job", "JobStatus", "ReviewCard", "SearchHit", "Task"]
