# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠ Critical orientation: there are TWO kernels

This is the single biggest source of confusion in the repo. The build scripts and
canonical code are in **`kernel/`**. A second, pre-migration copy of the backend lives in
**`synapse-engine/`** plus the **top-level** `contracts/`, `features/`, `jobs/`, `workers/`,
`editor_core/`, and `additional_features/` directories.

- **`kernel/`** (canonical): what `package.json` and all `uv run --directory kernel` scripts
  point at. Edges are real but most capability bodies are `NotImplementedError` stubs.
  Only `kb` (retrieval), `reason` (answering), and `code` (Code Buddy) are implemented — and
  `reason`/`code` now run **generative** when a model is reachable (litellm → Ollama/Anthropic),
  falling back to the extractive floor otherwise.
- **Legacy tree** (`synapse-engine/` + top-level python dirs): the *richer* reference
  implementation (full 31-tool MCP catalog, FSRS spaced-repetition, planner/ontology, vault
  gatekeeper, full retrieval/rerank, an 11-verb CLI). The migration plan (`IMPLEMENTATION_STATUS.md`
  §3, milestone **M0**) is to **port these bodies into `kernel/` one capability at a time, then
  delete the legacy copies.** `additional_features/` and `editor_core/` are explicitly out of
  scope ("quarantine"/"keep out").

When adding backend capability, work in `kernel/` and consult the legacy tree for the richer
logic to port. Do **not** edit the legacy tree expecting it to run in the cockpit.

## Commands

All commands run from the repo root. JS/TS is managed by **Bun** (workspaces); Python by **uv**.

```bash
# Install
bun install                                   # links @synapse/* workspaces
cd kernel && uv venv && uv pip install -e ".[dev]" && cd ..   # ML extras opt-in: ".[ml,dev]"
# Generative reasoning (Ask/Code Buddy) needs the `ai` extra + a model:
#   uv pip install -e ".[ai,dev]"   and  Ollama running (default ollama/qwen2.5:7b) or an Anthropic key.
#   Without them, reason/code degrade to the extractive floor (still correct, never fabricates).

# Run (all use the kernel/ canonical backend)
bun run dev          # REST edge + async worker + cockpit frontend (concurrently)
bun run dev:api      # FastAPI REST edge only, on :8765
bun run dev:worker   # drain the SQLite job queue
bun run dev:mcp      # FastMCP edge over stdio (usually launched by an MCP client)
bun run dev:cockpit  # cockpit Vite frontend only
bun run dev:desktop  # full Tauri desktop shell (compiles Rust on first run)

# Checks
bun run typecheck                             # typecheck all TS workspaces
bun run test:kernel                           # kernel pytest smoke tests
uv run --no-sync --directory kernel pytest tests/test_smoke.py::test_name   # single test
uv run --no-sync --directory kernel ruff check .     # lint (dev extra)
uv run --no-sync --directory kernel mypy src         # types (dev extra)

# Verify a running edge
curl http://127.0.0.1:8765/health             # with `bun run dev:api` up
```

The standalone `synapse-engine/` has its own `make` targets (`make ingest-sample`, `make ask
Q="..."`, `make test`) — these drive the *legacy* CLI engine, not the cockpit.

## Architecture

**Local-first, edge-mediated.** A Python kernel exposes capabilities over two edges; every
surface (desktop cockpit, AR glasses, Obsidian, editors, CLI) consumes an edge and never
touches kernel internals.

- **MCP edge** (`kernel/src/synapse_engine/mcp_server.py`) — the *primary* surface, FastMCP over stdio.
- **REST edge** (`kernel/src/synapse_engine/api_server.py`) — a *thin* FastAPI adapter for surfaces that
  can't speak MCP. Both edges are thin adapters that validate input against the shared
  `contracts` Pydantic models and call the **same in-process capability**, so they cannot drift.

**Capability layout** (`kernel/`): edges → capabilities (`src/synapse_engine/{kb,reason,ingest,study}`)
+ in-proc features (`features/{capture,pdf,planner,sr}.py`) → async work via the job queue
(`jobs/queue.py`) drained by a worker process (`workers/worker.py`). New job kinds are registered
in `HANDLERS` in `worker.py`.

**Data as truth.** All knowledge is Markdown in an Obsidian-compatible vault (`data/vault`).
SQLite indexes (`data/db/{index,jobs,sr}.db`) are **derived and rebuildable**. Config is in
`kernel/src/synapse_engine/config.py` — every path is overridable via `SYNAPSE_`-prefixed env vars
(e.g. `SYNAPSE_VAULT_DIR`). `data/` is git-ignored.

### Two principles that shape the code

1. **Degradation floors — never fabricate.** Every capability has an offline, dependency-free
   "floor" behind the same signature as its richer form. `kb.search()` runs a BM25 scan over the
   Markdown vault (the upgrade is FTS5 + `sqlite-vec` vectors fused with RRF). `reason.answer()`
   and `code.assist()` go through the `llm.py` seam (`complete() → str | None`): when a model
   answers they return a **generative**, grounded answer with citations; when litellm is absent or
   no model is reachable, `complete()` returns `None` and they fall back to the **extractive
   floor** — the answer **is** the top-ranked source chunks, never invented. Callers don't move
   when an upgrade lands. Preserve this everywhere: a missing dependency, dead model, or empty
   vault must degrade cleanly (`None` / `[]` / a floor answer), never raise.

2. **Vault write-safety (gatekeeper).** The Markdown vault is non-ACID and editable out-of-band
   by Obsidian. Writes must go through a serialized single-writer thread with optimistic
   concurrency checks. This is **not yet built in `kernel/`** (tracked as M0→M2); the legacy tree
   has the reference. Until it exists, capabilities that write the vault (`capture`, ingest) are
   stubs — do not add ad-hoc vault writes.

### Contracts must stay in sync

The Pydantic models in `kernel/contracts/models.py` are the source of truth for every shape that
crosses an edge (`SearchHit`, `Job`, `ReasonAnswer`, `Citation`, etc.). They are **manually
mirrored** to TypeScript in `packages/contracts-ts/index.ts`. When you change one, update the
other. The single typed client `packages/client/src/index.ts` (`@synapse/client`) is the only place
surfaces call the REST edge — surfaces never hand-roll `fetch`.

### Frontend (the wired paths + the gate)

**Two** cockpit views are wired end-to-end; they are the template for the rest:

```
AskView      → @synapse/client.ask()       → POST /reason/ask  → reason.answer() → kb.search()
CodeBuddyView→ @synapse/client.codeAssist()→ POST /code/assist → code.assist()   → kb.search()
```

Code Buddy is an editable **CodeMirror IDE** (`apps/cockpit/src/components/CodeEditor.tsx`): it
embeds your pasted code into the query, and `lib/parseAnswer.ts` splits the answer's fenced code
blocks into editable editors. The other six views (Capture, Planner, Review, Study, Notes, Vault)
are presentational **mock data** — design done, wiring not.

The cockpit **feature-gates** to kernel-wired views: each `VIEWS` entry has a `ready` flag
(`apps/cockpit/src/views/index.ts`) and `featureFlags.ts` hides non-ready views in dev, so local
testing surfaces only working features. Flip `ready: true` when a view's slice lands;
`VITE_SYNAPSE_ONLY_READY=0` reveals the mocks.

Scaling a view: implement the kernel capability in `kernel/`, expose it on both edges, add the
typed client method (+ contract if the shape is new), replace the mock, flip `ready: true`.

## Where to read more

- `IMPLEMENTATION_STATUS.md` — living tracker of what is actually built vs. stubbed, the
  two-kernels reconciliation (§3), and the milestone checklist. **Read this before scaling work.**
- `PROJECT_ARCHITECTURE.md` — the as-built kernel design.
- `SYSTEM_ARCHITECTURE.md` — the target Bun-monorepo design.
- `GAP_CLOSURE_PLAN.md` — sequenced plan (fix invariants before features).
