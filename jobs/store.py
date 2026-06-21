"""Persistent job store (§6) — SQLite-backed, stdlib only.

A 20-minute transcription must survive a kernel restart, so job state lives in
SQLite, not memory. This is the huey-recommended-by-default invariant honored
with zero extra infra (§6.1): one SQLite file, no daemon, offline-capable. The
queue backend (this in-proc default vs huey/RQ) is swappable behind the job
protocol (§4.6), so surfaces never see the choice.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

QUEUED, RUNNING, DONE, FAILED, CANCELLED = (
    "queued", "running", "done", "failed", "cancelled",
)
_LIVE = (QUEUED, RUNNING, DONE)  # statuses an idempotent submit dedupes onto


def content_hash(kind: str, payload: Dict[str, Any]) -> str:
    """Stable digest of (tool + args) for idempotent dedupe (§6.2)."""
    blob = json.dumps({"kind": kind, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass
class Job:
    job_id: str
    kind: str
    status: str
    payload: Dict[str, Any]
    payload_hash: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[float] = None
    attempts: int = 0
    created: float = 0.0
    started: Optional[float] = None
    updated: float = 0.0


class JobStore:
    def __init__(self, db_path: Path) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()  # serialize writes on the shared connection
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._init()

    def _init(self) -> None:
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id       TEXT PRIMARY KEY,
                kind         TEXT NOT NULL,
                status       TEXT NOT NULL,
                payload      TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                result       TEXT,
                error        TEXT,
                progress     REAL,
                attempts     INTEGER NOT NULL DEFAULT 0,
                created      REAL NOT NULL,
                started      REAL,
                updated      REAL NOT NULL
            )
            """
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, created)"
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(payload_hash)"
        )
        self._db.commit()

    # -- submission --------------------------------------------------------
    def create(self, kind: str, payload: Dict[str, Any], *, dedupe: bool = True) -> Job:
        """Insert a queued job, or return the existing live one for the same
        (kind, payload) so a re-submitted ingest dedupes instead of re-running."""
        h = content_hash(kind, payload)
        with self._lock:
            if dedupe:
                row = self._db.execute(
                    "SELECT * FROM jobs WHERE payload_hash=? AND status IN (?,?,?) "
                    "ORDER BY created DESC LIMIT 1",
                    (h, *_LIVE),
                ).fetchone()
                if row is not None:
                    return self._row_to_job(row)
            now = time.time()
            job = Job(job_id=str(uuid.uuid4()), kind=kind, status=QUEUED,
                      payload=payload, payload_hash=h, created=now, updated=now)
            self._db.execute(
                "INSERT INTO jobs (job_id,kind,status,payload,payload_hash,"
                "attempts,created,updated) VALUES (?,?,?,?,?,?,?,?)",
                (job.job_id, kind, QUEUED, json.dumps(payload), h, 0, now, now),
            )
            self._db.commit()
            return job

    # -- worker side -------------------------------------------------------
    def claim_next(self) -> Optional[Job]:
        """Atomically pick the oldest queued job and mark it running."""
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM jobs WHERE status=? ORDER BY created LIMIT 1", (QUEUED,)
            ).fetchone()
            if row is None:
                return None
            now = time.time()
            self._db.execute(
                "UPDATE jobs SET status=?, started=?, updated=?, attempts=attempts+1 "
                "WHERE job_id=?",
                (RUNNING, now, now, row["job_id"]),
            )
            self._db.commit()
            job = self._row_to_job(row)
            job.status = RUNNING
            job.started = now
            job.attempts += 1
            return job

    def set_progress(self, job_id: str, progress: float) -> None:
        self._update(job_id, progress=progress)

    def finish(self, job_id: str, result: Dict[str, Any]) -> None:
        self._update(job_id, status=DONE, result=result, progress=1.0)

    def fail(self, job_id: str, error: str) -> None:
        self._update(job_id, status=FAILED, error=error)

    def cancel(self, job_id: str) -> bool:
        """Best-effort cancel: only queued jobs are stopped (a running handler
        can't be force-killed in-process)."""
        with self._lock:
            row = self._db.execute(
                "SELECT status FROM jobs WHERE job_id=?", (job_id,)
            ).fetchone()
            if row is None or row["status"] != QUEUED:
                return False
            self._db.execute(
                "UPDATE jobs SET status=?, updated=? WHERE job_id=?",
                (CANCELLED, time.time(), job_id),
            )
            self._db.commit()
            return True

    # -- reads -------------------------------------------------------------
    def get(self, job_id: str) -> Optional[Job]:
        row = self._db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return self._row_to_job(row) if row else None

    def list(self, limit: int = 50) -> List[Job]:
        rows = self._db.execute(
            "SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_job(r) for r in rows]

    # -- helpers -----------------------------------------------------------
    def _update(self, job_id: str, **fields: Any) -> None:
        fields["updated"] = time.time()
        sets, vals = [], []
        for key, val in fields.items():
            sets.append(f"{key}=?")
            vals.append(json.dumps(val) if key == "result" else val)
        vals.append(job_id)
        with self._lock:
            self._db.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE job_id=?", vals)
            self._db.commit()

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        return Job(
            job_id=row["job_id"], kind=row["kind"], status=row["status"],
            payload=json.loads(row["payload"]), payload_hash=row["payload_hash"],
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"], progress=row["progress"], attempts=row["attempts"],
            created=row["created"], started=row["started"], updated=row["updated"],
        )
