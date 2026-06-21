"""Capture (§4.4) — pull external material into the KB.

web_ingest (trafilatura) and mail_ingest (Gmail, read-only) are sync;
audio_ingest (faster-whisper) is async and returns a job ticket.
"""
from .audio import audio_ingest_submit
from .mail import mail_ingest
from .web import web_ingest

__all__ = ["web_ingest", "audio_ingest_submit", "mail_ingest"]
