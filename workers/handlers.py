"""Async job handlers (§6, §14).

Each handler is the *worker* body for an async tool. Heavy dependencies are
imported lazily inside the handler so the module imports cleanly without them; a
missing dep fails the job with a clear error (surfaced via ``job_status``) rather
than crashing the worker. This is the real seam where Docling / faster-whisper /
ocrmypdf plug in.
"""
from __future__ import annotations

import subprocess
from typing import Any, Dict

from jobs.registry import JobContext, register


def _ingest_markdown(markdown: str, source: str, *, kind: str) -> str:
    """Route extracted text through the kernel ingest pipeline → KB + vault.
    Returns a doc_id. Kept here so all heavy handlers share one landing path."""
    from synapse_engine.config import Config
    from synapse_engine.ingest.pipeline import ingest_markdown_text  # see note below

    return ingest_markdown_text(markdown, source=source, kind=kind, config=Config.load())


@register("pdf_ingest")
def pdf_ingest_handler(payload: Dict[str, Any], ctx: JobContext) -> Dict[str, Any]:
    """Parse PDF → markdown → KB. Heuristic router: native pymupdf4llm first,
    Docling for math/tables (M1/M2). For now the native path is wired; Docling is
    the documented escalation behind the same handler."""
    src = payload["path_or_url"]
    ctx.progress(0.1)
    try:
        import pymupdf4llm
    except ImportError as exc:
        raise RuntimeError("pdf_ingest needs pymupdf4llm (pip install pymupdf4llm)") from exc
    markdown = pymupdf4llm.to_markdown(src)
    ctx.progress(0.7)
    doc_id = _ingest_markdown(markdown, source=src, kind="pdf")
    ctx.progress(1.0)
    return {"doc_id": doc_id, "markdown": markdown[:2000], "pages": markdown.count("\f") + 1}


@register("pdf_ocr")
def pdf_ocr_handler(payload: Dict[str, Any], ctx: JobContext) -> Dict[str, Any]:
    """OCR a scanned PDF with ocrmypdf (CLI, subprocess for memory isolation)."""
    path = payload["path"]
    out = payload.get("output_path") or f"{path}_ocr.pdf"
    cmd = ["ocrmypdf"]
    langs = payload.get("languages")
    if langs:
        cmd += ["-l", "+".join(langs)]
    cmd += ["--force-ocr", path, out]
    ctx.progress(0.1)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ocrmypdf failed: {proc.stderr.strip()[:500]}")
    ctx.progress(1.0)
    return {"out_path": out}


@register("audio_ingest")
def audio_ingest_handler(payload: Dict[str, Any], ctx: JobContext) -> Dict[str, Any]:
    """Transcribe audio with faster-whisper → KB."""
    path = payload["path"]
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("audio_ingest needs faster-whisper") from exc
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(path)
    parts = []
    for seg in segments:
        parts.append(seg.text)
        ctx.progress(min(0.95, len(parts) / 200))  # coarse, segment-count based
    transcript = " ".join(p.strip() for p in parts).strip()
    doc_id = _ingest_markdown(transcript, source=path, kind="transcript")
    ctx.progress(1.0)
    return {"doc_id": doc_id, "transcript": transcript}


@register("reindex")
def reindex_handler(payload: Dict[str, Any], ctx: JobContext) -> Dict[str, Any]:
    """Rebuild the derived index from the vault (the index is disposable, §11)."""
    from synapse_engine.config import Config
    from synapse_engine.ingest.pipeline import ingest_path

    config = Config.load()
    ctx.progress(0.1)
    result = ingest_path(config.vault_dir, config, write_vault=False)
    ctx.progress(1.0)
    return result
