"""Async workers (§14) — out-of-band consumers for model-heavy / unbounded work.

Importing this package (or ``workers.handlers``) registers the job handlers with
the shared registry. Results land in the index directly (it's derived) and any
vault mutation goes through the gatekeeper (§6.2), never straight to disk.
"""
