"""Async PDF capabilities — thin submission seams (§4.2).

These only *submit* to the persistent job queue and return a ticket; the actual
work lives in ``workers/handlers.py`` (the worker body), per the planner
keep-thin rule applied to capabilities. The previous version returned a
throwaway UUID that pointed at nothing — now the job_id is real and pollable via
``job_status``.
"""
from __future__ import annotations

from contracts.jobs import JobSubmitResponse
from contracts.pdf import PdfIngestInput, PdfOcrInput
from jobs import get_default_queue


def pdf_ingest_submit(input_data: PdfIngestInput) -> JobSubmitResponse:
    """Submit a PDF for parse → markdown → KB. Routes to pymupdf4llm / Docling
    in the worker."""
    return get_default_queue().submit("pdf_ingest", input_data.model_dump())


def pdf_ocr_submit(input_data: PdfOcrInput) -> JobSubmitResponse:
    """Submit a scanned PDF for OCR (ocrmypdf, in the worker)."""
    return get_default_queue().submit("pdf_ocr", input_data.model_dump())
