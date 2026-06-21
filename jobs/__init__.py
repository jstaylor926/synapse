"""Async job subsystem — persistent store + queue behind the §4.6 protocol.

A process-wide default queue is provided for convenience so async tools can
submit without threading config through every call. The kernel may build its own
``JobQueue`` against ``config.data_dir`` and share that instead.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Optional

from .queue import JobQueue
from .registry import JobContext, get_handler, known_kinds, register
from .store import Job, JobStore, content_hash

__all__ = [
    "JobQueue", "JobStore", "Job", "JobContext",
    "register", "get_handler", "known_kinds", "content_hash",
    "get_default_queue", "default_db_path",
]

_DEFAULT: Optional[JobQueue] = None
_LOCK = threading.Lock()


def default_db_path() -> Path:
    data = Path(os.environ.get("SYNAPSE_DATA_DIR", Path.cwd() / "data")).resolve()
    data.mkdir(parents=True, exist_ok=True)
    return data / "jobs.db"


def get_default_queue() -> JobQueue:
    """Lazily build the process-wide queue and ensure handlers are registered."""
    global _DEFAULT
    if _DEFAULT is None:
        with _LOCK:
            if _DEFAULT is None:
                # Import handlers for their @register side effects (lazy to avoid
                # a circular import at module load).
                import workers.handlers  # noqa: F401
                _DEFAULT = JobQueue(JobStore(default_db_path()))
    return _DEFAULT
