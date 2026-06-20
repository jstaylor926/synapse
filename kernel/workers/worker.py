"""The worker loop.

Claims jobs from the queue and dispatches them to the matching handler. New job
kinds are registered in `HANDLERS`. Run with `python -m workers.worker`.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from contracts.models import Job
from jobs.queue import JobQueue

POLL_SECONDS = 1.0


def _handle_ingest_web(job: Job) -> None:
    from synapse_engine.ingest import ingest_web

    ingest_web(job.payload["url"])


def _handle_ingest_pdf(job: Job) -> None:
    from synapse_engine.ingest import ingest_pdf

    ingest_pdf(job.payload["path"])


def _handle_transcribe(job: Job) -> None:
    from synapse_engine.ingest import ingest_audio

    ingest_audio(job.payload["path"])


HANDLERS: dict[str, Callable[[Job], None]] = {
    "ingest_web": _handle_ingest_web,
    "ingest_pdf": _handle_ingest_pdf,
    "transcribe": _handle_transcribe,
}


def run_once(queue: JobQueue) -> bool:
    """Process a single job if one is available. Returns True if it did work."""
    job = queue.claim()
    if job is None:
        return False
    handler = HANDLERS.get(job.kind)
    try:
        if handler is None:
            raise ValueError(f"No handler registered for job kind {job.kind!r}")
        handler(job)
        queue.complete(job.id)
    except Exception as exc:  # noqa: BLE001 — record and move on
        queue.fail(job.id, str(exc))
    return True


def main() -> None:
    queue = JobQueue()
    print("[synapse-worker] draining jobs; Ctrl-C to stop.")
    try:
        while True:
            if not run_once(queue):
                time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\n[synapse-worker] stopped.")


if __name__ == "__main__":
    main()
