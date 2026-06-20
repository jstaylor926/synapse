# Gap Closure Plan

The repository is scaffolded with runnable edges and stubs. This tracks the work
to turn the stubs into the real system. Each item points at the file(s) to fill in.

## Kernel — retrieval & ingest
- [ ] `kernel/src/synapse_engine/kb/__init__.py` — build the FTS5 + sqlite-vec index and implement `search()` (RRF is already wired).
- [ ] `kernel/src/synapse_engine/ingest/__init__.py` — implement `ingest_web` (trafilatura), `ingest_pdf` (pymupdf4llm/Docling), `ingest_audio` (faster-whisper).
- [ ] Index builder + watcher that (re)builds `data/db/index.db` from the vault.

## Kernel — reasoning
- [ ] `kernel/src/synapse_engine/reason/__init__.py` — grounded QA via litellm (Ollama default, Anthropic upgrade).

## Kernel — features
- [ ] `kernel/features/sr.py` — FSRS-6 via `py-fsrs`, persisted to `data/db/sr.db`.
- [ ] `kernel/features/planner.py` — parse the vault ontology; schedule blocks against Google Calendar (read-only).
- [ ] `kernel/features/capture.py` + **Vault Gatekeeper** — serialized single-writer with optimistic concurrency checks.
- [ ] `kernel/features/pdf.py` — PDF → Markdown.

## Kernel — edges
- [ ] Expand MCP tools in `mcp_server.py` (study, planner, capture) as features land.
- [ ] Expand REST endpoints in `api_server.py` to match what glasses-bridge/CLI need (`/study/due`, `/spec_view/*`).

## Surfaces
- [ ] `apps/cockpit` — connect to the MCP edge via an MCP client library; build the cockpit UI on `@synapse/ui-kit`.
- [ ] `apps/cockpit` — integrate TipTap editor.
- [ ] `packages/ui-kit` — establish the design system + shared components.
- [ ] `packages/contracts-ts` — automate generation from the Pydantic JSON Schema.
- [ ] `extensions/obsidian-synapse` — planner + due-cards views.
- [ ] `extensions/zed-synapse` — wire the code assistant to the knowledge base.

## Ops
- [ ] CI: `bun run typecheck`, `bun run test:kernel`, `ruff`, `mypy`.
- [ ] Decide cross-platform launch for `dev:*` (currently via `uv run`).
