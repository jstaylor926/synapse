"""FastMCP edge — the primary capability surface for the kernel.

Run it directly (stdio transport, what most MCP clients expect):

    python -m synapse_engine.mcp_server

Tools here are thin adapters: they validate input via the shared Pydantic
contracts and delegate to the in-proc capabilities under `features/`, the
retrieval layer (`synapse_engine.kb`), and the job queue (`jobs/`).
"""

from __future__ import annotations

from fastmcp import FastMCP

from synapse_engine import __version__
from synapse_engine.config import get_settings

mcp = FastMCP("synapse-kernel")


@mcp.tool
def health() -> dict:
    """Liveness probe — confirms the kernel is reachable and shows its config."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "vault_dir": str(settings.vault_dir),
        "db_dir": str(settings.db_dir),
    }


@mcp.tool
def kb_search(query: str, k: int = 8) -> list[dict]:
    """Hybrid (lexical + semantic) search over the vault via RRF.

    Stub: wire this to `synapse_engine.kb.search` once the index is built.
    """
    from synapse_engine.kb import search

    return [hit.model_dump() for hit in search(query, k=k)]


@mcp.tool
def ingest_url(url: str) -> dict:
    """Enqueue a web article for ingestion into the vault.

    Stub: enqueues a job on the SQLite queue; a worker does the real work.
    """
    from jobs.queue import JobQueue

    job_id = JobQueue().enqueue("ingest_web", {"url": url})
    return {"job_id": job_id, "status": "queued"}


@mcp.tool
def code_assist(query: str, k: int = 8) -> dict:
    """Grounded coding help over your ingested code + docs (read-only)."""
    from synapse_engine.code import assist

    return assist(query, k=k).model_dump()


def main() -> None:
    get_settings().ensure_dirs()
    mcp.run()


if __name__ == "__main__":
    main()
