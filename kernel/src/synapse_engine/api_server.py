"""FastAPI edge — a thin REST adapter for surfaces that cannot speak MCP.

Primarily consumed by the AR glasses bridge (`apps/glasses-bridge`). Keep this
surface intentionally small; the MCP edge is the primary, richer contract.

Run it:

    python -m synapse_engine.api_server
    # or: uvicorn synapse_engine.api_server:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from synapse_engine import __version__
from synapse_engine.config import get_settings

app = FastAPI(title="Synapse REST edge", version=__version__)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "version": __version__, "vault_dir": str(settings.vault_dir)}


@app.get("/kb/search")
def kb_search(q: str, k: int = 8) -> dict:
    from synapse_engine.kb import search

    return {"query": q, "hits": [hit.model_dump() for hit in search(q, k=k)]}


def main() -> None:
    import uvicorn

    settings = get_settings()
    settings.ensure_dirs()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
