"""SQLite-backed persistent job queue.

Heavy/async work (Whisper transcription, Docling/OCR, PDF parsing) is enqueued
here and drained by the worker process under `workers/`. Backed by
`data/db/jobs.db` so jobs survive restarts.
"""

from jobs.queue import JobQueue

__all__ = ["JobQueue"]
