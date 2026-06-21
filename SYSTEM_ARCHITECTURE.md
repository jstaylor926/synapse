# System Architecture

> **Purpose:** Comprehensive architecture document for the fresh unified personal tooling platform repository, integrating the Python kernel with a modern `bun`-driven TypeScript/JavaScript monorepo for all frontends, extensions, and CLI tooling.

## 1. Overall Project Scope
A single, self-hosted, local-first platform consolidating study, reasoning, document processing, and planning into one cohesive system. 
- **Core Strategy:** The "kernel" exposes capabilities via MCP (Model Context Protocol) and a thin REST adapter. Surfaces (desktop app, AR glasses, Obsidian, code editors) consume these edges but never touch the internals.
- **Offline & Local-First:** Built to function fully offline using local models (Ollama, fastembed, faster-whisper) with graceful upgrades to cloud APIs (Anthropic) when available.
- **Data as Truth:** All knowledge lives as standard Markdown in an Obsidian-compatible vault. The internal SQLite indexes are derived and rebuildable.

## 2. Tech Stack
- **Package Management (JS/TS):** **Bun** — Acts as the monorepo workspace manager, script runner, and ultrafast package installer for all UI, CLI, and extension surfaces.
- **Package Management (Python):** `uv` or `pip` — Manages the kernel, workers, and ML dependencies.
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

## 4. Optimal Directory Structure (Bun Monorepo)
To best utilize `bun` workspaces and cleanly separate the Python kernel from the JS/TS surfaces, the new repository should be structured as follows:

```text
the-project/
├── package.json               # Bun workspace root (defines "workspaces": ["apps/*", "packages/*", "extensions/*"])
├── bun.lockb                  # Bun binary lockfile
├── bunfig.toml                # Bun configuration
├── kernel/                    # The Python Backend (formerly synapse-engine)
│   ├── pyproject.toml         # Python dependencies
│   ├── src/synapse_engine/    # FastMCP, FastAPI, Ingest, KB, Reason, Study
│   ├── contracts/             # Shared Pydantic models
│   ├── features/              # In-proc capabilities (pdf, sr, capture, planner)
│   ├── jobs/                  # SQLite job queue logic
│   └── workers/               # Async worker execution process
├── packages/                  # Shared TS/JS libraries
│   ├── contracts-ts/          # TypeScript types generated/mirrored from Python Pydantic models
│   └── ui-kit/                # Shared React components and Design System
├── apps/                      # Primary Surfaces
│   ├── cockpit/               # Tauri + React desktop app (run via `bun run dev`)
│   ├── glasses-bridge/        # G2 spec_view adapter or web-app
│   └── cli/                   # Node/Bun CLI for interacting with the system
├── extensions/                # Editor plugins and third-party integrations
│   ├── obsidian-synapse/      # Obsidian plugin to interact with the planner/sr
│   └── zed-synapse/           # Zed extension
├── data/                      # Local data (Ignored in git)
│   ├── vault/                 # The Markdown truth (Obsidian vault)
│   └── db/                    # index.db, jobs.db, sr.db
└── docs/                      # Documentation
    └── architecture/          # SYSTEM_ARCHITECTURE.md, GAP_CLOSURE_PLAN.md
```

## 5. Setup Instructions (All Phases)

### Phase 1: Monorepo & Bun Initialization
1. Initialize the root directory:
   ```bash
   git init
   bun init -y
   ```
2. Update `package.json` to configure Bun workspaces:
   ```json
   {
     "name": "the-project",
     "workspaces": ["apps/*", "packages/*", "extensions/*"]
   }
   ```
3. Scaffold the directories:
   ```bash
   mkdir -p apps/cockpit packages/contracts-ts extensions kernel data/vault docs
   ```

### Phase 2: Python Kernel Setup
1. Move the existing `synapse-engine`, `contracts`, `features`, `jobs`, and `workers` into the `kernel/` directory.
2. Unify the Python dependencies into a single `kernel/pyproject.toml`.
3. Set up the Python virtual environment:
   ```bash
   cd kernel
   uv venv # or python -m venv .venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```
4. Verify the FastMCP server runs:
   ```bash
   python -m synapse_engine.mcp_server
   ```

### Phase 3: Tauri Cockpit Setup (Bun)
1. Initialize the Tauri application inside the `apps/` directory using Bun:
   ```bash
   cd apps
   bun create tauri-app cockpit --manager bun --template react-ts
   ```
2. Install UI dependencies:
   ```bash
   cd cockpit
   bun install
   ```
3. Establish the connection to the FastMCP server via an MCP client library in the Tauri app.

### Phase 4: Contracts & Surfaces
1. **Types:** Generate or manually mirror the Pydantic contracts from `kernel/contracts/` to TypeScript interfaces in `packages/contracts-ts/`. This ensures the UI components in `bun` match the Python backend perfectly.
2. **Glasses App:** Move the `spec_view` repository into `apps/glasses/` and configure it to query the FastAPI REST edge (`api_server.py`).
3. **Obsidian & Zed:** Move existing extensions into `extensions/` and link their dependencies via Bun workspaces if they are TS/JS based.
4. **Run the Stack:** Add a root `bun run dev` script in the top-level `package.json` that uses a tool like `concurrently` to boot the Python FastMCP server, the REST API, and the Tauri frontend simultaneously.

```json
// Root package.json example
"scripts": {
  "dev:kernel": "cd kernel && source .venv/bin/activate && python -m synapse_engine.mcp_server",
  "dev:cockpit": "bun --cwd apps/cockpit tauri dev",
  "dev": "concurrently \"bun run dev:kernel\" \"bun run dev:cockpit\""
}
```
