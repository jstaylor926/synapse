"""A minimal, dependency-free SQLite persistent job queue.

This is intentionally small and self-contained (stdlib `sqlite3` only) so the
kernel boots without the heavy ML extras installed. Workers claim jobs
atomically via an `UPDATE ... RETURNING` guarded by the QUEUED status.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from contracts.models import Job, JobStatus
from synapse_engine.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}',
    status      TEXT NOT NULL DEFAULT 'queued',
    attempts    INTEGER NOT NULL DEFAULT 0,
    error       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status, created_at);
"""


class JobQueue:
    def __init__(self, db_path: str | None = None) -> None:
        settings = get_settings()
        settings.db_dir.mkdir(parents=True, exist_ok=True)
        self._path = db_path or str(settings.jobs_db)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def enqueue(self, kind: str, payload: dict | None = None) -> str:
        job_id = uuid.uuid4().hex
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO jobs (id, kind, payload) VALUES (?, ?, ?)",
                (job_id, kind, json.dumps(payload or {})),
            )
        return job_id

    def claim(self) -> Job | None:
        """Atomically claim the oldest queued job and mark it RUNNING."""
        with self._conn() as conn:
            row = conn.execute(
                """
                UPDATE jobs SET status = 'running', attempts = attempts + 1
                WHERE id = (
                    SELECT id FROM jobs WHERE status = 'queued'
                    ORDER BY created_at LIMIT 1
                )
                RETURNING *
                """
            ).fetchone()
        return _row_to_job(row) if row else None

    def complete(self, job_id: str) -> None:
        self._set_status(job_id, JobStatus.DONE)

    def fail(self, job_id: str, error: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status = 'failed', error = ? WHERE id = ?",
                (error, job_id),
            )

    def get(self, job_id: str) -> Job | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None

    def _set_status(self, job_id: str, status: JobStatus) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status = ? WHERE id = ?", (status.value, job_id)
            )


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        kind=row["kind"],
        payload=json.loads(row["payload"]),
        status=JobStatus(row["status"]),
        attempts=row["attempts"],
        error=row["error"],
    )
