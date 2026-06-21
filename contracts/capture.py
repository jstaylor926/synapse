"""Capture tool contracts (§4.4).

`web_ingest` (trafilatura) and `mail_ingest` (Gmail, read-only) are sync.
`audio_ingest` (faster-whisper) is async: it returns a `JobSubmitResponse`
(see contracts.jobs) and the transcript lands as `AudioIngestResult`.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class WebIngestInput(BaseModel):
    url: str


class WebIngestOutput(BaseModel):
    doc_id: str
    markdown: str


class AudioIngestInput(BaseModel):
    path: str


class AudioIngestResult(BaseModel):
    doc_id: str
    transcript: str


class MailIngestInput(BaseModel):
    # Exactly one of thread_id / query identifies the *specific* item to pull.
    thread_id: Optional[str] = None
    query: Optional[str] = None


class MailIngestOutput(BaseModel):
    doc_id: str
    markdown: str
