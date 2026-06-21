"""Job handler registry.

Async tools submit a job of some ``kind``; a worker looks the kind up here and
runs the registered handler. Workers register their handlers (`workers/`); the
kernel only needs the queue + this registry to dispatch.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

# A handler takes (payload, ctx) and returns a JSON-serializable result dict.
# ``ctx`` exposes ctx.progress(fraction) for coarse progress reporting (§6.2).
Handler = Callable[[Dict[str, Any], "JobContext"], Dict[str, Any]]

_HANDLERS: Dict[str, Handler] = {}


def register(kind: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        _HANDLERS[kind] = fn
        return fn
    return deco


def get_handler(kind: str) -> Handler:
    if kind not in _HANDLERS:
        raise KeyError(f"No job handler registered for kind={kind!r}")
    return _HANDLERS[kind]


def known_kinds() -> list[str]:
    return sorted(_HANDLERS)


class JobContext:
    """Passed to handlers for progress reporting; more hooks land here later."""

    def __init__(self, job_id: str, on_progress: Callable[[float], None]) -> None:
        self.job_id = job_id
        self._on_progress = on_progress

    def progress(self, fraction: float) -> None:
        self._on_progress(max(0.0, min(1.0, fraction)))
