"""Async worker execution process.

Runs as a separate process from the edges, draining the SQLite job queue and
executing heavy ingestion work (Whisper, Docling, OCR). Start it with:

    python -m workers.worker
"""
