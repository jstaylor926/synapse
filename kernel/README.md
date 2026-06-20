# Synapse Kernel

The Python backend. Exposes platform capabilities over two edges:

- **FastMCP** (`synapse_engine.mcp_server`) — primary edge for the cockpit, Obsidian, and editors.
- **FastAPI** (`synapse_engine.api_server`) — thin REST edge for the AR glasses bridge.

Surfaces consume these edges and never reach into the internals.

## Layout

| Path | Responsibility |
| --- | --- |
| `src/synapse_engine/` | Edges (`mcp_server`, `api_server`) + capabilities: `ingest`, `kb` (RRF retrieval), `reason`, `study` |
| `contracts/` | Shared Pydantic models (mirrored to `packages/contracts-ts`) |
| `features/` | In-proc capabilities: `pdf`, `sr` (FSRS-6), `capture`, `planner` |
| `jobs/` | SQLite persistent job queue |
| `workers/` | Async worker process that drains the queue |

## Setup

```bash
cd kernel
uv venv                      # or: python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"   # core edges + tooling

# Heavy ingest/ML stack is opt-in:
uv pip install -e ".[ml,dev]"
```

## Run

```bash
python -m synapse_engine.mcp_server     # MCP edge (stdio)
python -m synapse_engine.api_server     # REST edge (uvicorn on :8765)
python -m workers.worker                # async job worker
pytest                                  # smoke tests (no ML extras needed)
```

## Configuration

All settings read from `SYNAPSE_`-prefixed env vars (or a `.env`). Defaults point
at the repo-local `../data/` tree. See `src/synapse_engine/config.py` and
`.env.example`.
