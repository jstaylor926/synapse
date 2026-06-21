"""audio_ingest (§4.4) — audio/lecture → transcript → KB (faster-whisper).

Async by the §3.1 rule (model-heavy, unbounded latency): this only submits a job
and returns a ticket; the transcription runs in ``workers/handlers.py`` and the
transcript lands via ``job_status`` → result.
"""
from __future__ import annotations

from contracts.capture import AudioIngestInput
from contracts.jobs import JobSubmitResponse
from jobs import get_default_queue


def audio_ingest_submit(inp: AudioIngestInput) -> JobSubmitResponse:
    return get_default_queue().submit("audio_ingest", inp.model_dump())
