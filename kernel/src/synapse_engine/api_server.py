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

from fastapi import HTTPException

from contracts.models import ExtractRequest, GradeRequest, ReasonAsk, SaveCardsRequest

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


@app.post("/code/assist")
def code_assist(body: ReasonAsk) -> dict:
    from synapse_engine.code import assist

    return assist(body.question, k=body.k).model_dump()


@app.post("/study/extract")
def study_extract(body: ExtractRequest) -> dict:
    from synapse_engine.study import extract

    return extract(body.topic, kind=body.kind, n=body.n, k=body.k).model_dump()


@app.post("/study/save")
def study_save(body: SaveCardsRequest) -> dict:
    """Persist a generated deck so its cards become gradable (idempotent)."""
    from synapse_engine.study import save_flashcards

    return {"ids": save_flashcards(body.deck, body.cards)}


@app.get("/study/due")
def study_due(deck: str | None = None, limit: int = 20) -> dict:
    """Cards due for review now, most-urgent first."""
    from synapse_engine.study import due_cards

    return {"cards": [c.model_dump() for c in due_cards(limit=limit, deck=deck)]}


@app.post("/study/grade")
def study_grade(body: GradeRequest) -> dict:
    """Grade a review (1=Again..4=Easy) and return the next due time."""
    from synapse_engine.study import grade

    try:
        return grade(body.card_id, body.rating).model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown card_id {exc}") from exc


def main() -> None:
    import uvicorn

    settings = get_settings()
    settings.ensure_dirs()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
