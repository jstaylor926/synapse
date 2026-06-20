"""Smoke tests that don't require the heavy ML extras."""

from __future__ import annotations

import tempfile
from pathlib import Path

from jobs.queue import JobQueue
from synapse_engine.kb import reciprocal_rank_fusion


def test_rrf_fuses_rankings() -> None:
    scores = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "d"]])
    # "a" and "b" appear high in both rankings, so they should outrank the rest.
    ranked = sorted(scores, key=scores.get, reverse=True)
    assert ranked[:2] == ["b", "a"] or ranked[:2] == ["a", "b"]


def test_job_queue_roundtrip() -> None:
    # Use a directory (not NamedTemporaryFile) so SQLite can open the path on
    # Windows, where the temp file would otherwise be held open exclusively.
    with tempfile.TemporaryDirectory() as tmp:
        q = JobQueue(db_path=str(Path(tmp) / "jobs.db"))
        job_id = q.enqueue("ingest_web", {"url": "https://example.com"})
        claimed = q.claim()
        assert claimed is not None
        assert claimed.id == job_id
        assert claimed.kind == "ingest_web"
        q.complete(job_id)
        assert q.get(job_id).status.value == "done"
        # nothing left to claim
        assert q.claim() is None
