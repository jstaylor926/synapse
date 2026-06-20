# System Architecture

> **Purpose:** Comprehensive architecture document for the unified personal tooling
> platform repository (`synapse`), integrating the Python kernel with a modern
> `bun`-driven TypeScript/JavaScript monorepo for all frontends, extensions, and
> CLI tooling.

## 1. Overall Project Scope
A single, self-hosted, local-first platform consolidating study, reasoning, document processing, and planning into one cohesive system.
- **Core Strategy:** The "kernel" exposes capabilities via MCP (Model Context Protocol) and a thin REST adapter. Surfaces (desktop app, AR glasses, Obsidian, code editors) consume these edges but never touch the internals.
- **Offline & Local-First:** Built to function fully offline using local models (Ollama, fastembed, faster-whisper) with graceful upgrades to cloud APIs (Anthropic) when available.
- **Data as Truth:** All knowledge lives as standard Markdown in an Obsidian-compatible vault. The internal SQLite indexes are derived and rebuildable.

## 2. Tech Stack
- **Package Management (JS/TS):** **Bun** — monorepo workspace manager, script runner, and package installer for all UI, CLI, and extension surfaces.
- **Package Management (Python):** `uv` — manages the kernel, workers, and ML dependencies.
- **Kernel / Edge:** Python, FastMCP (primary edge), FastAPI (REST edge for AR glasses).
- **Retrieval & DB:** SQLite (FTS5 + `sqlite-vec` for vector search), Python-based hybrid RRF (Reciprocal Rank Fusion).
- **Heavy Compute / Async:** In-house SQLite persistent job queue for processing (Whisper, Docling, OCR).
- **Frontend / Surfaces:** Tauri + React (Desktop Cockpit), TipTap (Editor).
- **AI / ML:** `litellm` (Anthropic + Ollama), `fastembed` (embeddings), `faster-whisper` (audio), `pymupdf4llm` / Docling (PDF).

## 3. Features
1. **Knowledge Base Ingestion:** Async processing of PDFs, web articles (via `trafilatura`), and audio (via `faster-whisper`) into clean Markdown stored in the vault.
2. **Hybrid Retrieval (RRF):** Fuses lexical (BM25 via FTS5) and semantic (vector cosine) search, optionally reranked via a cross-encoder model.
3. **Planner & Ontology:** Vault-native entity tracking (tasks, assignments, topics). Dynamically schedules blocks against real-world deadlines (Google Calendar read-only sync).
4. **Spaced Repetition (FSRS-6):** Tracks study decay natively via `py-fsrs`. Renders flashcards and walking-quizzes.
5. **Vault Gatekeeper:** A serialized, single-writer thread protecting the non-ACID Markdown vault from concurrent internal writes, utilizing optimistic concurrency checks against direct Obsidian edits.
6. **Code Assistant:** Context-aware assistant integrated into editors (Zed) backed by the ingested knowledge base.

## 4. Directory Structure (Bun Monorepo)

This reflects the repository as scaffolded.

```text
synapse/
├── package.json               # Bun workspace root ("workspaces": ["apps/*", "packages/*", "extensions/*"])
├── bun.lock                   # Bun lockfile
├── bunfig.toml                # Bun configuration
├── tsconfig.json              # Shared TS base config (packages extend it)
├── kernel/                    # The Python backend (the "kernel")
│   ├── pyproject.toml         # Python dependencies (core edges + optional ML extras)
│   ├── src/synapse_engine/    # mcp_server, api_server, ingest, kb (RRF), reason, study
│   ├── contracts/             # Shared Pydantic models
│   ├── features/              # In-proc capabilities (pdf, sr, capture, planner)
│   ├── jobs/                  # SQLite job queue
│   ├── workers/               # Async worker execution process
│   └── tests/                 # Smoke tests (no ML extras needed)
├── packages/                  # Shared TS/JS libraries
│   ├── contracts-ts/          # @synapse/contracts-ts — TS mirror of the Pydantic models
│   └── ui-kit/                # @synapse/ui-kit — shared React components / design system
├── apps/                      # Primary surfaces
│   ├── cockpit/               # @synapse/cockpit — Tauri v2 + React desktop app
│   ├── glasses-bridge/        # @synapse/glasses-bridge — adapts the REST edge for AR glasses (G2 spec_view)
│   └── cli/                   # @synapse/cli — Bun CLI for interacting with the system
├── extensions/                # Editor plugins and third-party integrations
│   ├── obsidian-synapse/      # @synapse/obsidian-synapse — Obsidian plugin (planner / SR)
│   └── zed-synapse/           # Zed extension (Rust/WASM — not a Bun workspace)
├── data/                      # Local data (git-ignored)
│   ├── vault/                 # The Markdown truth (Obsidian vault)
│   └── db/                    # index.db, jobs.db, sr.db
└── docs/                      # Documentation
    └── architecture/          # SYSTEM_ARCHITECTURE.md, GAP_CLOSURE_PLAN.md
```

## 5. The two edges

| Edge | Module | Transport | Primary consumers |
| --- | --- | --- | --- |
| **MCP** (primary) | `synapse_engine.mcp_server` | stdio | cockpit, Obsidian, Zed — launched by each MCP client |
| **REST** (thin) | `synapse_engine.api_server` | HTTP `:8765` | glasses-bridge, CLI |

Surfaces speak only to these edges. Internals (`ingest`, `kb`, `features`, `jobs`)
are never imported across the process boundary.

## 6. Running the stack

See the root `README.md` for setup. In short:

```bash
bun install                                  # JS/TS workspaces
cd kernel && uv venv && uv pip install -e ".[dev]" && cd ..   # Python kernel
bun run dev                                  # REST edge + worker + cockpit frontend
```

`bun run dev` uses `concurrently` to boot the REST API, the async worker, and the
cockpit Vite frontend. The MCP edge (`bun run dev:mcp`) is normally launched by an
MCP client rather than the dev orchestrator. `bun run dev:desktop` runs the full
Tauri shell (compiles Rust on first run).
