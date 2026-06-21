# Synapse — Implementation Status & Integration Tracker

> **Updated:** 2026-06-20 · **Branch:** `update-claude`
>
> Living status of *what is actually built*, *how to run it*, and *what's left* to
> connect every module into the Tauri cockpit. Companion to `PROJECT_ARCHITECTURE.md`
> (the as-built kernel design) and `SYSTEM_ARCHITECTURE.md` (the target Bun monorepo).
> This file is the **navigation map + progress tracker** — tick the checkboxes as you go.

---

## 0. TL;DR — what works *right now*

The **Ask view is wired end-to-end** with real data (the first vertical slice):

```
AskView (React)
  → @synapse/client.ask()
    → POST http://127.0.0.1:8765/reason/ask   (FastAPI REST edge, CORS-allowed)
      → reason.answer()  →  kb.search()        (BM25 over data/vault/*.md)
        → grounded answer + citations
          → rendered in the Neo-Gonzo Noir UI
```

Everything else in the cockpit (Code, Capture, Planner, Review, Study, Notes, Vault) is
**presentational with mock data** — the design is done, the wiring is not. The kernel
serves `kb_search` and `reason_ask` for real (extractive/lexical floor, offline, zero ML
deps); all other capabilities are `NotImplementedError` stubs in the canonical kernel.

---

## 1. Progress scoreboard (the metric)

| Track | Done | Total | % | Notes |
|---|---|---|---|---|
| **Cockpit views wired to kernel** | 1 | 8 | 12% | Ask ✅ — the rest are mock UIs |
| **REST endpoints implemented** | 3 | ~25 | 12% | `/health`, `/kb/search`, `/reason/ask` |
| **MCP tools implemented** | 3 | ~31 | 10% | `health`, `kb_search`, `ingest_url` |
| **Kernel capability bodies (real)** | 2 | 8 | 25% | `kb`, `reason` real; `study/sr/planner/capture/pdf/ingest` stub |
| **Async infra** | 2 | 2 | 100% | job queue ✅ + worker loop ✅ (handlers still stub) |
| **Shared TS packages** | 3 | 3 | 100% | `contracts-ts`, `ui-kit`, `client` (types partial) |
| **Other surfaces functional** | 2 | 4 | 50% | cli ✅, glasses-bridge ✅; obsidian ⚠ (calls a missing endpoint), zed skeleton |
| **Kernel reconciliation (M0)** | 0 | 1 | 0% | two parallel kernels still coexist — see §3 |

> **Headline:** the *plumbing pattern* is proven (1 view, 1 client, 3 endpoints). Scaling
> to the other 7 views is now mostly mechanical — **once the kernel duplication is resolved**.

---

## 2. Quickstart — spin it up & test

### 2.1 Prerequisites
- **Bun** ≥ 1.3 — JS/TS workspace manager + runner
- **uv** (Python 3.11+) — kernel env/deps
- **Rust** (rustup) — *only* for the native Tauri desktop window (`dev:desktop`)

### 2.2 Install (first time)
```bash
# 1. JS/TS workspaces (links @synapse/* packages)
bun install

# 2. Python kernel — core edges only; the Ask slice needs NO ML extras
cd kernel
uv venv
uv pip install -e ".[dev]"        # later, for quality: uv pip install -e ".[ml,dev]"
cd ..
```

### 2.3 Run
```bash
bun run dev          # boots REST edge :8765 + async worker + cockpit (Vite :1420)
```
Then **either**:
- open **http://localhost:1420** in a browser (fastest — no Rust compile), **or**
- run `bun run dev:desktop` for the native Tauri window (compiles Rust on first run).

Go to **Ask** → type *"How does simulated annealing differ from a genetic algorithm?"* →
**SEND**. You should get a grounded, cited answer drawn from the seeded vault notes.

Per-surface scripts:

| Command | What it does |
|---|---|
| `bun run dev:api` | FastAPI REST edge on `:8765` |
| `bun run dev:worker` | Drain the SQLite job queue |
| `bun run dev:cockpit` | Cockpit Vite frontend only (`:1420`) |
| `bun run dev:desktop` | Full Tauri desktop shell |
| `bun run dev:mcp` | MCP edge over stdio (for LLM clients, not the GUI) |
| `bun run typecheck` | Typecheck all TS workspaces |
| `bun run test:kernel` | Kernel pytest smoke tests |

### 2.4 Verify the backend directly
```bash
curl http://127.0.0.1:8765/health
curl "http://127.0.0.1:8765/kb/search?q=simulated%20annealing&k=3"
curl -X POST http://127.0.0.1:8765/reason/ask \
     -H "content-type: application/json" \
     -d '{"question":"simulated annealing vs genetic algorithm","k":3}'
```

### 2.5 Seed data (so Ask returns real results)
The vault (`data/vault/`) is **git-ignored** (Data-as-Truth is machine-local). Two seed
notes already exist locally for the demo:
- `data/vault/notes/sa-vs-ga.md`
- `data/vault/resources/lecture-07.md`

A fresh clone starts with an empty vault → Ask honestly returns *"No matching notes…"*.
Add `.md` files to `data/vault/` to populate it. (Real `kb_ingest`/`web_ingest` lands later.)

### 2.6 Troubleshooting
| Symptom | Cause / fix |
|---|---|
| Ask shows *"request failed · is the kernel running?"* | Start `bun run dev:api` (or `bun run dev`). |
| Ask returns *"No matching notes in the vault yet"* | Vault is empty — add `.md` files to `data/vault/`. |
| CORS error in browser console | Origin not in `api_cors_origins` (`kernel/.../config.py`); add it. |
| Port 8765 in use | A previous `dev:api` is still running — stop it. |
| Worker marks ingest jobs `failed` | Expected — `ingest_*` handlers are still stubs (§4). |

---

## 3. ⚠ Critical orientation: there are TWO kernels

This is the single biggest source of confusion. Resolve it before scaling.

| | `kernel/` (canonical) | `synapse-engine/` + top-level `contracts|features|jobs|workers/` (legacy) |
|---|---|---|
| **Role** | The target. Build scripts point here (`--directory kernel`). | Pre-migration reference with the *richer* bodies. |
| **MCP lib** | `fastmcp>=2.0` | old `mcp>=1.2` |
| **MCP tools** | 3 (health, kb_search, ingest_url) | full 31-tool catalog |
| **REST** | `/health`, `/kb/search`, `/reason/ask` (+ CORS) | flashcards-only shim |
| **Capabilities** | `kb`+`reason` real; rest **stubbed** | sr (FSRS), planner+ontology, gatekeeper, full retrieval/rerank, reason engine — **implemented** |
| **CLI** | none | 11 verbs |

**Decision (recommended):** make `kernel/` canonical; **port the real bodies** from the
legacy tree into `kernel/features|kb|reason` one capability at a time, then **delete** the
legacy copies. Tracked as **M0** in §5. Until then, only `kb`/`reason` are real in the kernel.

Also still present and **out of the kernel path** (your own C1/C2 calls): `additional_features/`
(~25 extra PDF ops — quarantine) and `editor_core/` (OT editor experiment — keep out).

---

## 4. Current implementation status (detailed)

### 4.1 Kernel capabilities (`kernel/`)
| Module | File | State | Notes |
|---|---|---|---|
| Retrieval | `src/synapse_engine/kb/__init__.py` | ✅ **real** | BM25 lexical floor over the vault; RRF helper present. sqlite-vec/FTS5/embeddings are the upgrade. |
| Reasoning | `src/synapse_engine/reason/__init__.py` | ✅ **real** | Extractive floor (answer = top chunks + citations, never fabricates). LLM via litellm is the upgrade. |
| Job queue | `jobs/queue.py` | ✅ **real** | SQLite persistent; atomic claim via `UPDATE…RETURNING`. Smoke-tested. |
| Worker loop | `workers/worker.py` | ◐ **loop real, handlers stub** | claim→dispatch→complete/fail works; `ingest_*` handlers raise. |
| Study | `src/synapse_engine/study/__init__.py` | ⛔ stub | `due_cards()` raises. |
| Spaced rep | `features/sr.py` | ⛔ stub | `review()` raises. Real FSRS body in legacy tree. |
| Planner | `features/planner.py` | ⛔ stub | `open_tasks()`, `schedule_blocks()` raise. Real ontology in legacy tree. |
| Capture | `features/capture.py` | ⛔ stub | `capture_note()` raises. Needs the gatekeeper. |
| PDF | `features/pdf.py` | ⛔ stub | `to_markdown()` raises. |
| Ingest | `src/synapse_engine/ingest/__init__.py` | ⛔ stub | `ingest_web/pdf/audio()` raise. |
| Config | `src/synapse_engine/config.py` | ✅ real | paths + edge host/port + `api_cors_origins`. |

### 4.2 REST edge (`kernel/src/synapse_engine/api_server.py`)
| Method | Path | State | Backs |
|---|---|---|---|
| GET | `/health` | ✅ | config / liveness |
| GET | `/kb/search?q=&k=` | ✅ | `kb.search` |
| POST | `/reason/ask` | ✅ | `reason.answer` |
| — | everything else (§5) | ⛔ | to build |

CORS scoped to the cockpit origins (`localhost:1420`, `tauri://localhost`, …); bound to `127.0.0.1`.

### 4.3 MCP edge (`kernel/src/synapse_engine/mcp_server.py`)
`health` ✅ · `kb_search` ✅ (now live via `kb.search`) · `ingest_url` ◐ (enqueues a real job;
the worker handler is a stub). The other ~28 catalog tools are not yet registered here.
*MCP is for LLM clients — the cockpit uses REST, not MCP.*

### 4.4 Cockpit views (`apps/cockpit/src/views/`)
| View | Wired? | Backend it needs |
|---|---|---|
| **Ask** | ✅ live | `/kb/search`, `/reason/ask` |
| Code | ⛔ mock | `POST /code/assist` (code_assist capability — not in kernel yet) |
| Capture | ⛔ mock | `POST /capture/web|audio`, `POST /pdf/ingest` (async + job poll) |
| Planner | ⛔ mock | `GET /plan/agenda`, `POST /plan/breakdown|schedule|run` |
| Review | ⛔ mock | `GET /sr/due`, `POST /sr/review`, `GET /sr/stats` |
| Study | ⛔ mock | `POST /study/flashcards|quiz|cheatsheet` |
| Notes | ⛔ mock | `GET/PUT /vault/note` (via gatekeeper) |
| Vault | ⛔ mock | `GET /vault/tree`, `/kb/search` |
| *(chrome)* TitleBar / DegradationLadder | ⛔ mock | `GET /health`, `GET /jobs` |

### 4.5 Shared packages & other surfaces
| Package | State | Notes |
|---|---|---|
| `packages/ui-kit` (Neo-Gonzo Noir) | ✅ complete | full component set + tokens. |
| `packages/contracts-ts` | ◐ partial | types for SearchHit/Job/Task/ReviewCard/Citation/ReasonAnswer; missing study/planner/capture/pdf. |
| `packages/client` (`@synapse/client`) | ✅ new | `health/searchKb/ask` + base-URL resolution. **The integration seam — all surfaces should use it.** |
| `apps/cli` | ✅ works | `health`, `search` → real endpoints. |
| `apps/glasses-bridge` | ✅ works | proxies `/spec_view/search` → `/kb/search`. |
| `extensions/obsidian-synapse` | ⚠ broken | calls `GET /study/due` which **doesn't exist yet** (build it or repoint). |
| `extensions/zed-synapse` | ◐ skeleton | Rust/WASM stub; not wired. |

---

## 5. What's left to implement (tracked)

### M0 — Reconcile the kernels (do first; unblocks everything) ⬜
- [ ] Confirm `kernel/` as canonical; freeze the legacy tree.
- [ ] Port `sr` (FSRS-6 body + `data/db/sr.db`) from legacy → `kernel/features/sr.py`.
- [ ] Port `planner` + vault **ontology** + **gatekeeper** → `kernel/features/planner.py` (+ a `kb/gatekeeper.py`).
- [ ] Port `capture` (web via trafilatura) + `ingest_web` body → `kernel/.../ingest`.
- [ ] Port `study.due_cards`/flashcards/quiz/cheatsheet.
- [ ] Delete legacy `synapse-engine/`, top-level `contracts|features|jobs|workers/` once parity confirmed.
- [ ] Quarantine `additional_features/`; keep `editor_core/` out of the kernel path.
- [ ] Update `contracts-ts` to cover every ported contract.

### REST edge buildout (one thin adapter per capability) ⬜
- [ ] `GET /sr/due` · `POST /sr/review` · `GET /sr/stats`  → unblocks **Review** + fixes obsidian ext
- [ ] `POST /study/flashcards` · `/study/quiz` · `/study/cheatsheet`  → **Study**
- [ ] `GET /plan/agenda` · `POST /plan/breakdown` · `/plan/schedule` · `/plan/run`  → **Planner**
- [ ] `POST /capture/web` · `/capture/audio` (async) · `POST /pdf/ingest` (async)  → **Capture**
- [ ] `GET /jobs` · `GET /jobs/{id}`  → async badges + polling
- [ ] `POST /code/assist`  → **Code**
- [ ] `GET /vault/tree` · `GET /vault/note` · `PUT /vault/note`  → **Notes / Vault**

### View wiring (repeat the Ask recipe — §6) ⬜
- [x] **Ask**
- [ ] Review · [ ] Study · [ ] Planner · [ ] Capture · [ ] Code · [ ] Notes · [ ] Vault
- [ ] TitleBar + DegradationLadder → live `/health` + `/jobs`

### Quality upgrades (behind the same signatures) ⬜
- [ ] Embeddings: `HashEmbedder` floor → `fastembed`; vector store via `sqlite-vec` + FTS5 + RRF.
- [ ] LLM: extractive floor → `litellm` (Ollama offline / Anthropic with key); citations preserved.
- [ ] Reranker: inline bounded cross-encoder (`SYNAPSE_RERANK`).
- [ ] Structure-aware chunking (markdown headers/AST + tree-sitter for code).
- [ ] Real ingest worker handlers (pymupdf4llm / faster-whisper / trafilatura).
- [ ] Google Calendar read-only for the planner.

### Packaging / hardening ⬜
- [ ] Tauri **sidecar**: PyInstaller-bundle the kernel; spawn api+worker from Rust on launch (self-contained desktop app).
- [ ] Tighten the REST edge for non-dev use (already localhost-bound; add a shared secret if exposed).
- [ ] Declare all lazy ML deps honestly in `kernel/pyproject.toml` extras.

---

## 6. The reusable recipe (how to wire any view)

The Ask slice established the pattern. Each remaining view is the same 4 steps:

1. **Kernel route** — add a thin handler in `api_server.py` that validates input with a
   `contracts` model and calls the in-proc capability, returning `.model_dump()`.
2. **Client fn** — add a typed function to `packages/client/src/index.ts`.
3. **Types** — mirror any new shapes in `packages/contracts-ts/src/index.ts`.
4. **View** — swap the mock array in `apps/cockpit/src/views/<View>.tsx` for client calls
   (state + `useState`/effects; async views also poll `GET /jobs/{id}`).

> If the capability is a stub in `kernel/`, do its M0 port first — otherwise the route 500s.

---

## 7. File map (where things live)

```
kernel/                              # canonical Python kernel
  src/synapse_engine/
    api_server.py   ← REST edge (CORS + 3 routes)        [edit here to add endpoints]
    mcp_server.py   ← MCP edge (3 tools)
    config.py       ← paths, ports, api_cors_origins
    kb/__init__.py        ✅ BM25 retrieval floor
    reason/__init__.py    ✅ extractive answer floor
    study/__init__.py     ⛔ stub
    ingest/__init__.py    ⛔ stubs
  features/{sr,planner,capture,pdf}.py   ⛔ stubs (real bodies in legacy tree)
  jobs/queue.py          ✅ SQLite job queue
  workers/worker.py      ◐ loop real, handlers stub
  contracts/models.py    ← shared Pydantic contracts
packages/
  client/         ← @synapse/client (the integration seam)   [add client fns here]
  contracts-ts/   ← TS mirror of Pydantic contracts          [mirror new types here]
  ui-kit/         ← Neo-Gonzo Noir design system (complete)
apps/
  cockpit/src/views/*.tsx   ← 8 views (Ask wired, rest mock) [wire views here]
  cli/  ·  glasses-bridge/   ← functional REST consumers
extensions/  obsidian-synapse (⚠) · zed-synapse (skeleton)
data/vault/      ← Markdown truth (git-ignored, local)
synapse-engine/ + top-level contracts|features|jobs|workers/   ← LEGACY (to reconcile)
additional_features/ · editor_core/   ← quarantined / experimental
```

---

## 8. Known caveats
- **Extractive/lexical floor only** — no embeddings, LLM, or rerank yet (all opt-in upgrades behind the same signatures).
- **Vault is git-ignored** — the demo seeds are local; fresh clones see an empty vault.
- **Dual kernel** — the legacy tree still holds the richer bodies; M0 reconciles this.
- **obsidian-synapse** calls a not-yet-built endpoint (`/study/due`).
- **No auth / single-user / local-first** by design.

---

*When reality and this doc disagree, fix one of them on purpose.*
