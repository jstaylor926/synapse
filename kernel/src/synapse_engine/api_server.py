"""FastAPI edge — a thin REST adapter for surfaces that cannot speak MCP.

Consumed by the desktop cockpit (`apps/cockpit`), the AR glasses bridge
(`apps/glasses-bridge`), the CLI, and the editor extensions. Each route is a
thin adapter that validates input with the shared `contracts` models and calls
the same in-process capability the MCP edge does — so the two edges can't drift.

Run it:

    python -m synapse_engine.api_server
    # or: uvicorn synapse_engine.api_server:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contracts.models import ReasonAsk

from synapse_engine import __version__
from synapse_engine.config import get_settings

app = FastAPI(title="Synapse REST edge", version=__version__)

# Allow the browser-based surfaces (the Tauri cockpit) to call the edge.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().api_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "version": __version__, "vault_dir": str(settings.vault_dir)}


@app.get("/kb/search")
def kb_search(q: str, k: int = 8) -> dict:
    from synapse_engine.kb import search

    return {"query": q, "hits": [hit.model_dump() for hit in search(q, k=k)]}


@app.post("/reason/ask")
def reason_ask(body: ReasonAsk) -> dict:
    from synapse_engine.reason import answer

    return answer(body.question, k=body.k).model_dump()


def main() -> None:
    import uvicorn

    settings = get_settings()
    settings.ensure_dirs()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
