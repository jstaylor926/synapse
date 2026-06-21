"""Job queue — submit + dispatch over the persistent store.

Default backend is an in-process worker thread: zero infra, runs offline, honors
the minimal-infra invariant. The architecture's escalation path (huey on SQLite,
then RQ/Redis under concurrency, §6.1) slots in behind this same API — surfaces
keep talking the §4.6 protocol either way.

For true crash isolation, run the worker as a separate process via
``workers/run.py`` instead of ``start_inproc_worker``; both consume the same store.
"""
from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Dict

from contracts.jobs import (
    JobCancelResponse,
    JobListItem,
    JobListResponse,
    JobStatusResponse,
    JobSubmitResponse,
)

from .registry import JobContext, get_handler
from .store import Job, JobStore


def _started_iso(job: Job) -> str | None:
    if not job.started:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(job.started))


class JobQueue:
    def __init__(self, store: JobStore) -> None:
        self.store = store
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None

    # -- boundary-facing (§4.6) -------------------------------------------
    def submit(self, kind: str, payload: Dict[str, Any]) -> JobSubmitResponse:
        job = self.store.create(kind, payload)
        return JobSubmitResponse(job_id=job.job_id, status=job.status)

    def status(self, job_id: str) -> JobStatusResponse:
        job = self.store.get(job_id)
        if job is None:
            return JobStatusResponse(job_id=job_id, status="failed",
                                     error="unknown job_id")
        return JobStatusResponse(job_id=job.job_id, status=job.status,
                                 progress=job.progress, result=job.result,
                                 error=job.error)

    def list(self, limit: int = 50) -> JobListResponse:
        return JobListResponse(jobs=[
            JobListItem(job_id=j.job_id, kind=j.kind, status=j.status,
                        started=_started_iso(j))
            for j in self.store.list(limit)
        ])

    def cancel(self, job_id: str) -> JobCancelResponse:
        return JobCancelResponse(job_id=job_id, cancelled=self.store.cancel(job_id))

    # -- worker side -------------------------------------------------------
    def run_once(self) -> bool:
        """Claim and run one job. Returns False if the queue was empty."""
        job = self.store.claim_next()
        if job is None:
            return False
        ctx = JobContext(job.job_id,
                         lambda f: self.store.set_progress(job.job_id, f))
        try:
            handler = get_handler(job.kind)
            result = handler(job.payload, ctx)
            self.store.finish(job.job_id, result or {})
        except Exception:  # never a silent drop (§6.2) — surface as failed
            self.store.fail(job.job_id, traceback.format_exc(limit=4))
        return True

    def start_inproc_worker(self, poll: float = 0.2) -> None:
        """Background consumer in this process (the default, offline path)."""
        if self._worker and self._worker.is_alive():
            return

        def loop() -> None:
            while not self._stop.is_set():
                if not self.run_once():
                    time.sleep(poll)

        self._stop.clear()
        self._worker = threading.Thread(target=loop, name="job-worker", daemon=True)
        self._worker.start()

    def run_forever(self, poll: float = 0.5) -> None:
        """Blocking consume loop — the entrypoint for a separate worker process."""
        while not self._stop.is_set():
            if not self.run_once():
                time.sleep(poll)

    def stop(self) -> None:
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=5)
