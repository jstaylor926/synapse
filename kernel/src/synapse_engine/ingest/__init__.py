"""Knowledge-base ingestion.

Turns PDFs, web articles, and audio into clean Markdown stored in the vault.
The heavy lifting (Whisper, Docling, OCR, trafilatura) runs out-of-process via
the job queue and workers; this package holds the parsing/cleaning logic those
workers call.
"""

from __future__ import annotations


def ingest_web(url: str) -> str:
    """Fetch and clean a web article into Markdown. Stub (uses trafilatura)."""
    raise NotImplementedError


def ingest_pdf(path: str) -> str:
    """Convert a PDF to Markdown. Stub (uses pymupdf4llm / Docling)."""
    raise NotImplementedError


def ingest_audio(path: str) -> str:
    """Transcribe audio to Markdown. Stub (uses faster-whisper)."""
    raise NotImplementedError
